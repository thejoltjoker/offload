import sys
import os
import shutil
from pathlib import Path

print('')
print(os.getcwd())
print('')

if sys.platform == 'darwin':
    APP_DATA_PATH = Path().home() / 'Library/Application Support/Offload'
elif sys.platform == 'win64':
    APP_DATA_PATH = Path().home() / 'Library/Application Support/Offload'
else:
    APP_DATA_PATH = Path(__file__).parent
REPORTS_PATH = APP_DATA_PATH / 'reports'
LOGS_PATH = APP_DATA_PATH / 'logs'
VERSION = '0.1.2b0'
EXCLUDE_FILES = ["MEDIAPRO.XML",
                 "Icon",
                 "STATUS.BIN",
                 "SONYCARD.IND",
                 "AVIN0001.INP",
                 "AVIN0001.BNP",
                 "MOVIEOBJ.BDM",
                 "PRV00001.BIN",
                 "INDEX.BDM",
                 "fseventsd-uuid",
                 ".dropbox.device",
                 "AVIN0001.INT",
                 "mdb.bk",
                 "mdb.db",
                 "Get_started_with_GoPro.url",
                 ".Spotlight-V100",
                 "VolumeConfiguration.plist",
                 "psid.db",
                 "indexState",
                 "0.indexHead",
                 "0.indexGroups",
                 "live.0.indexPostings",
                 "live.0.indexIds",
                 "live.0.indexBigDates",
                 "live.0.indexGroups",
                 "live.0.indexPositions",
                 "live.0.indexDirectory",
                 "live.0.indexCompactDirectory",
                 "live.0.indexArrays",
                 "live.0.shadowIndexHead",
                 "live.0.directoryStoreFile",
                 "live.0.directoryStoreFile.shadow",
                 "store.db",
                 ".store.db",
                 "reverseDirectoryStore",
                 "tmp.spotlight.state",
                 "shutdown_time",
                 "reverseDirectoryStore.shadow",
                 "0.shadowIndexHead",
                 "store.updates",
                 "permStore",
                 "live.1.indexHead",
                 "live.1.indexIds",
                 "0.shadowIndexGroups",
                 "live.1.indexUpdates",
                 "live.2.indexHead",
                 "live.2.indexIds",
                 "live.2.indexBigDates",
                 "live.2.indexGroups",
                 "live.0.shadowIndexGroups",
                 "reverseStore.updates",
                 "live.1.indexBigDates",
                 "tmp.spotlight.loc",
                 "live.1.indexGroups",
                 "live.1.indexPostings",
                 "live.1.indexTermIds",
                 "live.1.indexDirectory",
                 "live.1.indexCompactDirectory",
                 "live.1.indexArrays",
                 "live.2.indexPostings",
                 "live.1.directoryStoreFile",
                 "live.1.shadowIndexHead",
                 "live.1.shadowIndexTermIds",
                 "live.1.shadowIndexArrays",
                 "live.1.shadowIndexCompactDirectory",
                 "live.1.shadowIndexDirectory",
                 "live.1.directoryStoreFile.shadow",
                 "live.1.shadowIndexGroups",
                 "live.2.indexTermIds",
                 "live.2.indexPositions",
                 "live.2.indexPositionTable",
                 "live.2.indexDirectory",
                 "live.2.indexCompactDirectory",
                 "live.2.indexArrays",
                 "live.2.indexUpdates",
                 "live.2.directoryStoreFile",
                 "live.2.shadowIndexHead",
                 "live.2.shadowIndexTermIds",
                 "live.2.shadowIndexPositionTable",
                 "live.2.shadowIndexArrays",
                 "live.2.shadowIndexCompactDirectory",
                 "live.2.shadowIndexDirectory",
                 "live.2.directoryStoreFile.shadow",
                 "live.2.shadowIndexGroups",
                 "live.0.indexHead",
                 "journal.412",
                 "retire.411",
                 ".DS_Store",
                 "fseventsd-uuid.",
                 ".dropbox.device",
                 "Icon?",
                 "Icon\r.",
                 "Icon\r",
                 "store_generation.",
                 "store_generation.\r",
                 ".Spotlight-V100"]

_script_data = Path(os.getcwd()) / 'data'
_script_data.mkdir(parents=True, exist_ok=True)
shutil.copytree(_script_data, APP_DATA_PATH / 'data', dirs_exist_ok=True)
