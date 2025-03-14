FILES_TO_GET_V1 = [
    "0819_UkraineCombinedTweetsDeduped.csv",
    "0820_UkraineCombinedTweetsDeduped.csv",
    "0821_UkraineCombinedTweetsDeduped.csv",
    "0822_UkraineCombinedTweetsDeduped.csv",
    "0823_UkraineCombinedTweetsDeduped.csv",
    "0824_UkraineCombinedTweetsDeduped.csv",
    "0825_UkraineCombinedTweetsDeduped.csv",
    "0826_UkraineCombinedTweetsDeduped.csv",
    "0827_UkraineCombinedTweetsDeduped.csv",
    "0828_UkraineCombinedTweetsDeduped.csv"
]

FILES_TO_GET_V2 = [
    "0829_UkraineCombinedTweetsDeduped.csv",
    "0830_UkraineCombinedTweetsDeduped.csv",
    "0901_UkraineCombinedTweetsDeduped.csv",
    "0902_UkraineCombinedTweetsDeduped.csv",
    "0903_UkraineCombinedTweetsDeduped.csv",
    "0904_UkraineCombinedTweetsDeduped.csv",
    "0905_UkraineCombinedTweetsDeduped.csv",
    "0906_UkraineCombinedTweetsDeduped.csv",
    "0907_UkraineCombinedTweetsDeduped.csv",
    "0908_UkraineCombinedTweetsDeduped.csv",
    "0910_UkraineCombinedTweetsDeduped.csv",
    "0911_UkraineCombinedTweetsDeduped.csv",
    "0912_UkraineCombinedTweetsDeduped.csv",
    "0913_UkraineCombinedTweetsDeduped.csv",
]

FILES_TO_GET_V3 = [
    "0914_UkraineCombinedTweetsDeduped.csv",
    "0915_UkraineCombinedTweetsDeduped.csv",
    "0916_UkraineCombinedTweetsDeduped.csv",
    "0917_UkraineCombinedTweetsDeduped.csv",
    "0918_UkraineCombinedTweetsDeduped.csv",
    "0919_UkraineCombinedTweetsDeduped.csv",
    "0920_UkraineCombinedTweetsDeduped.csv",
    "0921_UkraineCombinedTweetsDeduped.csv",
    "0922_UkraineCombinedTweetsDeduped.csv",
    "0923_UkraineCombinedTweetsDeduped.csv",
    "0924_UkraineCombinedTweetsDeduped.csv",
    "0925_UkraineCombinedTweetsDeduped.csv"
    "0926_UkraineCombinedTweetsDeduped.csv",
    "0927_UkraineCombinedTweetsDeduped.csv",
    "0928_UkraineCombinedTweetsDeduped.csv",
    "0929_UkraineCombinedTweetsDeduped.csv",
    "0930_UkraineCombinedTweetsDeduped.csv",
    "0930_UkraineCombinedTweetsDeduped.csv"
]

FILES_GITHUB_PIPELINE_TEST_VERSION = [
    "0914_UkraineCombinedTweetsDeduped.csv"
]

def get_data_version(version):
    version_map = {
        1: FILES_TO_GET_V1,
        2: FILES_TO_GET_V2,
        3: FILES_TO_GET_V3,
        4: FILES_GITHUB_PIPELINE_TEST_VERSION
    }
    return version_map.get(version, False)

def get_data_version_name(version):
    version_map = {
        1: "../data/version_1",
        2: "../data/version_2",
        3: "../data/version_3",
        4: "../data/github_test_version"
    }
    return version_map.get(version, False)
