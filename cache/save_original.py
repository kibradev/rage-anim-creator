from pathlib import Path
import subprocess
Path('cache/original_posekeys.py').write_bytes(subprocess.check_output(['git','show','HEAD:pipeline/lib/posekeys.py']))
Path('cache/original_volleyball.py').write_bytes(subprocess.check_output(['git','show','HEAD:pipeline/clip_defs/volleyball.py']))
