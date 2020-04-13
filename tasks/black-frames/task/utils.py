from base64 import b64encode
from functools import reduce
from pprint import pformat
from time import gmtime, strftime


# parses the output of ffmpeg into a dictionary
def ffmpeg_black_frames_to_json(lines):
    lines = [x.split("] ")[1].rstrip() for x in lines if "blackdetect" in x]
    lines = [x.split(" ") for x in lines]
    lines = [list(map(lambda x: x.split(":"), x)) for x in lines]
    lines = [dict(x) for x in lines]

    return lines


# parses seconds expressed as floats into a suitable format for a VMAP file
def ffmpeg_time_from_seconds(seconds):
    try:
        ms = str(seconds).split(".")[1]
    except:
        ms = "000"
    return strftime("%H:%M:%S", gmtime(seconds)) + "." + str(ms)


# additional properties to each element
def hydrate_item(item):
    start = float(item["black_start"])
    end = float(item["black_end"])
    midpoint = (start + end) / 2.0

    item["timeOffset"] = ffmpeg_time_from_seconds(midpoint)
    item["breakId"] = str(b64encode(str(hash(pformat(item))).encode("utf-8")))

    return item


# generates adbreak tag for each item
def make_adbreak_tag(vars):
    return """<vmap:AdBreak timeOffset="{timeOffset}" breakType="linear" breakId="{breakId}">
    <vmap:AdSource id="ad-source-{breakId}" allowMultipleAds="false" followRedirects="true">
        <vmap:AdTagURI templateType="vast3"><![CDATA[https://pubads.g.doubleclick.net/gampad/ads?slotname=/124319096/external/ad_rule_samples&sz=640x480&ciu_szs=300x250&cust_params=deployment%%3Ddevsite%%26sample_ar%%3Dpremidpost&url=&unviewed_position_start=1&output=xml_vast3&impl=s&env=vp&gdfp_req=1&ad_rule=0&cue=15000&vad_type=linear&vpos=midroll&pod=2&mridx=1&rmridx=1&ppos=1&lip=true&min_ad_duration=0&max_ad_duration=30000&vrid=6256&video_doc_id=short_onecue&cmsid=496&kfa=0&tfcd=0]]></vmap:AdTagURI>
    </vmap:AdSource>
</vmap:AdBreak>""".format(
        **vars
    )


# generates a VMAP file
def make_ad_vmap(ads_list):
    begin = """<?xml version="1.0" encoding="UTF-8"?>
<vmap:VMAP xmlns:vmap="http://www.iab.net/videosuite/vmap" version="1.0">
    """
    ads_tags = reduce(lambda a, b: a + b, ads_list, "")

    end = "\n</vmap:VMAP>"

    return begin + ads_tags + end


# packages all together
def build_manifest(ffmpeg_black_frames):
    json_body = ffmpeg_black_frames_to_json(ffmpeg_black_frames)
    prepared_json = list(map(hydrate_item, json_body))
    tags = [make_adbreak_tag(x) for x in prepared_json]
    manifest = make_ad_vmap(tags)
    return manifest


if __name__ == "__main__":

    print("# FFMPEG Utils :: ffmpeg_black_frames_to_json")
    with open("../../../assets/ffmpeg-blackdetect-sample.txt", "r") as fp:
        lines = fp.readlines()

    json_body = ffmpeg_black_frames_to_json(lines)

    print(json_body)

    print("# FFMPEG Utils :: ffmpeg_time_from_seconds")
    durations = [float(x["black_start"]) for x in json_body]
    durations = map(ffmpeg_time_from_seconds, durations)
    print(list(durations))

    prepared_json = list(map(hydrate_item, json_body))

    print("# FFMPEG Utils :: ffmpeg_time_from_seconds")
    print(prepared_json)

    tags = [make_adbreak_tag(x) for x in prepared_json]
    manifest = make_ad_vmap(tags)

    with open("vmap.xml", "w") as fp:
        fp.write(manifest)
