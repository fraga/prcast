import json
import asyncio
import os
from pathlib import Path
import edge_tts
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pydub import AudioSegment

script = [
  {
    "speaker": "Andrew",
    "text": "Welcome back to PRCast. Today we're looking at Pull Request 5167 in the unified operations public repo. This one is from Milda Beinaryte, updating the bank revaluation documentation with some new enhancements."
  },
  {
    "speaker": "Andrew",
    "text": "The update adds details about enhancements to the feature, specifically around the setup requirements and some troubleshooting steps. It looks like a focused update, just one file changed, adding 21 lines. That should definitely help folks configuring their bank foreign currency revaluations."
  },
  {
    "speaker": "Andrew",
    "text": "Better setup and troubleshooting docs mean fewer headaches when dealing with multiple currencies. That's all for today, thanks for listening!"
  }
]

VOICE = "en-US-AndrewNeural"

base=Path('/home/rod/.openclaw/workspace/prcast')
repo='MicrosoftDocs/dynamics-365-unified-operations-public'
slug='microsoftdocs-dynamics-365-unified-operations-public'
pr=5167
id_=f'{slug}-pr-{pr}-solo'
audio_dir=base/'audio'/slug
audio_dir.mkdir(parents=True, exist_ok=True)
audio_file=f'{id_}.mp3'
audio_path=audio_dir/audio_file

async def generate_line(text, voice, filename):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

async def main():
    files = []
    print("Generating clips...")
    for i, line in enumerate(script):
        filename = f"/tmp/line_{i}_solo.mp3"
        await generate_line(line["text"], VOICE, filename)
        files.append(filename)

    print("Stitching audio...")
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=400)
    for f in files:
        combined += AudioSegment.from_mp3(f) + pause
        os.remove(f)

    combined.export(str(audio_path), format="mp3", bitrate="128k")

    size = audio_path.stat().st_size
    dur = int(len(combined) / 1000)

    pub_iso=datetime.now(timezone.utc).isoformat()
    pub_rfc=datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    pr_url=f'https://github.com/{repo}/pull/{pr}'
    title='PR #5167: Update bank revaluation documentation with enhancements (Solo Edition)'
    desc=('Pull Request by music727 (Milda Beinaryte): Added details about enhancements to bank foreign currency revaluation, including setup requirements and troubleshooting steps. 1 file changed, +21 -2 lines.')

    jpath=base/'feeds'/'episodes.json'
    arr=json.loads(jpath.read_text())
    arr=[e for e in arr if e.get('id')!=id_]
    arr.append({'id':id_,'repo':repo,'title':title,'description':desc,'audio_file':audio_file,'duration_seconds':dur,'pub_date':pub_iso,'pr_url':pr_url,'pr_number':pr})
    jpath.write_text(json.dumps(arr,indent=2)+"\n")

    ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
    ET.register_namespace('atom','http://www.w3.org/2005/Atom')
    ET.register_namespace('content','http://purl.org/rss/1.0/modules/content/')

    def add_item(ch,title_text,link,desc_text,guid,enclosure,pub,duration,size):
        item=ET.SubElement(ch,'item')
        ET.SubElement(item,'title').text=title_text
        ET.SubElement(item,'link').text=link
        ET.SubElement(item,'description').text=desc_text
        g=ET.SubElement(item,'guid',{'isPermaLink':'false'}); g.text=guid
        ET.SubElement(item,'enclosure',{'url':enclosure,'length':str(size),'type':'audio/mpeg'})
        ET.SubElement(item,'pubDate').text=pub
        ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text=str(duration)

    rpath=base/'feeds'/f'{slug}.xml'
    rt=ET.parse(rpath); ch=rt.getroot().find('channel')
    for it in list(ch.findall('item')):
        g=it.find('guid')
        if g is not None and g.text==id_:
            ch.remove(it)
    add_item(ch,title,pr_url,desc,id_,f'https://fraga.github.io/prcast/audio/{slug}/{audio_file}',pub_rfc,dur,size)
    ch.find('lastBuildDate').text=pub_rfc
    rt.write(rpath,encoding='UTF-8',xml_declaration=True)

    gpath=base/'feeds'/'prcast.xml'
    gt=ET.parse(gpath); gch=gt.getroot().find('channel')
    for it in list(gch.findall('item')):
        g=it.find('guid')
        if g is not None and g.text==id_:
            gch.remove(it)
    add_item(gch,f'[{repo}] {title}',pr_url,desc,id_,f'https://fraga.github.io/prcast/audio/{slug}/{audio_file}',pub_rfc,dur,size)
    gch.find('lastBuildDate').text=pub_rfc
    gt.write(gpath,encoding='UTF-8',xml_declaration=True)

    print('updated',audio_path,'dur',dur,'size',size)

if __name__ == "__main__":
    asyncio.run(main())
