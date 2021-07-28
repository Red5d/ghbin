import os, sys, stat, json, shutil, platform, requests, tempfile, tarfile, gzip, zipfile, magic
from pathlib import Path

class bcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Repo:
    def __init__(self, path):
        self.path = path
        self.fullpath = 'https://github.com/'+path
        r = s.get('https://api.github.com/repos/'+path, headers=headers, auth=(config['gh_user'],config['gh_token'])).json()
        self.name = r['name']
        self.desc = r['description']
        self.releaseInfo = {}

    # Get/return info about the latest release.
    def latestRelease(self):
        # Return cached release info if present
        if self.releaseInfo != {}:
            return self.releaseInfo
        else:
            r = s.get('https://api.github.com/repos/'+self.path+'/releases/latest', headers=headers, auth=(config['gh_user'],config['gh_token'])).json()
            release_type = "Release"
            if r['prerelease']:
                release_type = "Pre-Release"

            if len(r['name']) > 0:
                tagname = r['name']
            else:
                tagname = r['tag_name']

            releaseInfo = {
                'name': r['name'],
                'tagname': tagname,
                'release_type': release_type,
                'published_at': r['published_at'],
                'assets': r['assets']
            }

            # Cache release info
            self.releaseInfo = releaseInfo
            return releaseInfo

    # Print the basic repo info
    def printInfo(self):
        print(f"{bcolors.BOLD}{bcolors.UNDERLINE}{self.name}{bcolors.ENDC} - {bcolors.BOLD}{self.desc}{bcolors.ENDC}")

    # Print info about the latest release
    def printLatest(self):
        latestRelease = self.latestRelease()
        print(f"{bcolors.BOLD}{bcolors.UNDERLINE}{self.name}{bcolors.ENDC} - {bcolors.BOLD}{self.desc}{bcolors.ENDC}")
        print(f"{bcolors.WARNING}{latestRelease['tagname']}{bcolors.ENDC}: {latestRelease['release_type']} published {latestRelease['published_at']}")
        assetNum = 1
        for asset in latestRelease['assets']:
            if (os_name in asset['name'].lower() or (os_name == 'linux' and 'appimage' in asset['name'].lower())) and machine_arch in asset['name'].lower() and not (noarm in asset['name'].lower() or 'debian' in asset['content_type'] or 'rpm' in asset['content_type']):
                print(f"({assetNum})    {asset['name']} | {asset['content_type']} | {asset['browser_download_url']}")
                assetNum += 1

        print()


# Main program begin

config = {}
try:
    # Attempt to load config file
    with open(Path.home() / '.ghbin.json', 'r') as f:
        config = json.load(f)
except:
    # If no config file found, perform interactive initial setup
    print("Initial Setup")
    bindir = input("Enter a path to store the downloaded binaries: ")
    ghuser = input("Enter your GitHub username: ")
    ghtoken = input("Enter a GitHub personal access token: ")
    repos = []
    repoadd = input("Enter a GitHub repo to track release binaries from in the format <user>/<repo name>: ")
    while repoadd != "":
        try:
            Repo(repoadd)
            repos.append(repoadd)
        except:
            print("Invalid repository path")

        repoadd = input("Add another repo? (leave blank if no): ")

    with open(Path.home() / '.ghbin.json', 'w') as f:
        config = {
            'bin_dir': bindir,
            'gh_user': ghuser,
            'gh_token': ghtoken,
            'repos': repos
        }
        json.dump(config, f)

    print(f"Saved configuration to {Path.home() / '.ghbin.json'}")
    sys.exit()

# Check OS
os_name = platform.system().lower()
if 'win' in os_name:
    os_name = 'win'

# Check processor architecture
machine_arch = platform.machine()
if 'x86_64' in machine_arch:
    machine_arch = '64'
    noarm = 'arm'
elif 'arm' in machine_arch:
    # Maybe refine this to account for specific arm versions automatically
    machine_arch = 'arm'
    noarm = ''

# Create shared session object
s = requests.Session()

# Set header for GitHub API
headers = {'Accept': 'application/vnd.github.v3+json'}

def fileFilter(members):
    for tarinfo in members:
        if not bool([x for x in ['license', 'readme'] if x in tarinfo.name.lower()]):
            if tarinfo.isfile() or tarinfo.isdir():
                yield tarinfo

def installAsset(url):
    # Use a temporary directory for downloading and extracting the files
    with tempfile.TemporaryDirectory() as tmpdir:
        r = requests.get(url)
        assetPath = Path(os.path.join(tmpdir, url.split('/')[-1]))
        with open(assetPath, 'wb') as f:
            f.write(r.content)

        p = Path(assetPath)

        # If this is an AppImage, move it to the correct location and end the function with a 'return'
        if assetPath.parts[-1].endswith('.AppImage'):
            shutil.move(assetPath, os.path.join(config['bin_dir'], assetPath.parts[-1]))
            os.chmod(os.path.join(config['bin_dir'], assetPath.parts[-1]), 0o755)
            return
        else:
            # If this is a Gzip or XZ file, extract with tarfile
            if "gzip compressed data" in magic.from_file(str(assetPath)).lower() or "XZ compressed data" in magic.from_file(str(assetPath)).lower():
                try:
                    with tarfile.open(assetPath, 'r') as t:
                        t.extractall(path=str(p.parent), members=fileFilter(t))

                except tarfile.ReadError:
                    with gzip.open(assetPath, 'rb') as g:
                        with open(assetPath.parent / assetPath.parts[-1].split('.gz')[0], 'wb') as gzExtracted:
                            shutil.copyfileobj(g, gzExtracted)

            else:
                # If this is a Zip file, extract with zipfile
                with zipfile.ZipFile(assetPath, 'r') as zipFile:
                    zipFile.extractall(assetPath.parent)

        # For each item in the temp directory...
        for item in assetPath.parent.iterdir():
            # If the item is a file and not the downloaded compressed asset file
            if Path(item).is_file() and item != assetPath.parts[-1]:
                # ...and if it's a binary executable
                if "executable" in magic.from_file(str(item)):
                    # ...move it to the configured directory
                    shutil.move(item, os.path.join(config['bin_dir'], item.parts[-1]))
                    os.chmod(os.path.join(config['bin_dir'], item.parts[-1]), 0o755)
            elif Path(item).is_dir():
                # If the item is a directory instead, check each of the items in it
                for diritem in Path(item).iterdir():
                    # ...and if the item is a binary executable
                    if "executable" in magic.from_file(str(diritem)):
                        # ...move it to the configured directory
                        shutil.move(diritem, os.path.join(config['bin_dir'], diritem.parts[-1]))
                        os.chmod(os.path.join(config['bin_dir'], diritem.parts[-1]), 0o755)

# CLI argument parsing
if len(sys.argv) > 1:
    # Install command
    if sys.argv[1] == "install":
        # If the item name to install is found in the repos config...
        if sys.argv[2] in [x.split('/')[1] for x in config['repos']]:
            # Lookup the full repo path in the config, then print the release info
            r = Repo([x for x in config['repos'] if x.split('/')[1] == sys.argv[2]][0])
            r.printLatest()

            # Ask the user which of the available assets to use for installation
            targetNum = input("Enter the number to the left of the file above that you want to install (leave blank to use the first one): ")
            if targetNum == "":
                targetNum = 1
            else:
                targetNum = int(targetNum)
                
            # Retrieve and filter the asset list for compatible assets...
            compatibleAssets = []
            for asset in r.latestRelease()['assets']:
                if (os_name in asset['name'].lower() or (os_name == 'linux' and 'appimage' in asset['name'].lower())) and machine_arch in asset['name'].lower() and not (noarm in asset['name'].lower() or 'debian' in asset['content_type'] or 'rpm' in asset['content_type']):
                    compatibleAssets.append(asset)
            
            # ...then download and install the selected asset
            downloadUrl = compatibleAssets[targetNum-1]['browser_download_url']
            print(f"Downloading and installing {downloadUrl}...")
            installAsset(downloadUrl)

    # Add Repository command
    elif sys.argv[1] == "add":
        try:
            # Verify the repo path by attempting to pull data from it via the API
            Repo(sys.argv[2])
            # If it works, append it to the repos config and write the file back
            with open(Path.home() / '.ghbin.json', 'w') as f:
                config['repos'].append(sys.argv[2])
                json.dump(config, f)
        except:
            print("Invalid repository path")

    else:
        print("Usage: python ghbin.py [command] <app/repo>")
        print(f"Config File: {Path.home() / '.ghbin.json'}")
        print()
        print("A tool for installing applications distributed as binary releases on GitHub.")
        print()
        print("Run without parameters for a summary of all configured repositories.")
        print()
        print("Commands:")
        print("\tadd <repo path> - Add a GitHub repository to track with the format: user/reponame")
        print("\tinstall <app name> - Install an application from the configured repositories")
        print()
        print("Examples:")
        print("\tpython ghbin.py add owenthereal/ccat")
        print("\tpython ghbin.py install ccat")
        print()

# If no arguments given, list release info for all configured repos
else:
    for path in config['repos']:
        r = Repo(path)
        r.printLatest()

    
