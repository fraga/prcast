import json
import asyncio
import os
from pathlib import Path
import edge_tts
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pydub import AudioSegment

script = [
  {"speaker": "Andrew", "text": "Welcome to PRCast. Quick special edition: Dynamics 365 version ten point zero point forty seven is now in general availability for self-update in March twenty twenty six."},
  {"speaker": "Sarah", "text": "Right. Build number ten point zero point two five two seven. Preview started in January, with auto-update rollout in April."},
  {"speaker": "Andrew", "text": "Finance highlights include line level cancellation for general budget reservations, faster subscription billing batch processing, and general ledger period close enhancements."},
  {"speaker": "Sarah", "text": "Tax also got important performance improvements, plus multi-language support in the advanced tax calculation engine with version prerequisites."},
  {"speaker": "Andrew", "text": "On Supply Chain, there are major operational updates: inventory transaction consolidation, warehouse archiving improvements, glove mounted scanning support, and Entra Conditional Access in the Warehouse Management mobile app."},
  {"speaker": "Sarah", "text": "And a notable commerce update: pay by link moved from private preview in ten point zero point forty six to public preview in ten point zero point forty seven, including setup guidance for the Adyen connector and payment notifications."},
  {"speaker": "Andrew", "text": "Human Resources also advances with job and job title expiration, accrual adjustment support for terminated employees in preview, and the new LeaveBalanceActiveEntity to reduce duplicate personnel records."},
  {"speaker": "Sarah", "text": "Bottom line: ten point zero point forty seven is a practical release focused on performance, operational scale, and rollout readiness across Finance, Supply Chain, Commerce, and HR."},
]

VOICES = {
    "Andrew": "en-US-AndrewNeural",
    "Sarah": "en-US-JennyNeural"
}

base=Path('/home/rod/.openclaw/workspace/prcast')
repo='MicrosoftDocs/dynamics-365-unified-operations-public'
slug='microsoftdocs-dynamics-365-unified-operations-public'
episode_suffix='release-10-0-47-ga'
id_=f'{slug}-{episode_suffix}'
audio_dir=base/'audio'/slug
audio_dir.mkdir(parents=True, exist_ok=True)
audio_file=f'{id_}.mp3'
audio_path=audio_dir/audio_file

async def generate_line(text, voice, filename):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)

async def main():
    files = []
    for i, line in enumerate(script):
        filename = f"/tmp/prcast_10047_{i}.mp3"
        await generate_line(line["text"], VOICES[line["speaker"]], filename)
        files.append(filename)

    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=350)
    for f in files:
        combined += AudioSegment.from_mp3(f) + pause
        os.remove(f)

    combined.export(str(audio_path), format="mp3", bitrate="128k")

    size = audio_path.stat().st_size
    dur = int(len(combined) / 1000)

    pub_iso=datetime.now(timezone.utc).isoformat()
    pub_rfc=datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S +0000')
    link='https://github.com/MicrosoftDocs/dynamics-365-unified-operations-public'
    title='Release 10.0.47 GA: cross-app highlights (Finance, SCM, Commerce, HR)'
    desc=('Special episode summarizing Dynamics 365 Unified Operations 10.0.47 GA timeline and highlights across Finance, Supply Chain Management, Commerce, and Human Resources, including pay-by-link public preview and warehouse/mobile performance updates.')

    jpath=base/'feeds'/'episodes.json'
    arr=json.loads(jpath.read_text())
    arr=[e for e in arr if e.get('id')!=id_]
    arr.append({
        'id':id_,
        'repo':repo,
        'title':title,
        'description':desc,
        'audio_file':audio_file,
        'duration_seconds':dur,
        'pub_date':pub_iso,
        'pr_url':link
    })
    jpath.write_text(json.dumps(arr,indent=2)+"\n")

    ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
    ET.register_namespace('atom','http://www.w3.org/2005/Atom')

    def add_item(ch,title_text,link,desc_text,guid,enclosure,pub,duration,size):
        item=ET.SubElement(ch,'item')
        ET.SubElement(item,'title').text=title_text
        ET.SubElement(item,'link').text=link
        ET.SubElement(item,'description').text=desc_text
        g=ET.SubElement(item,'guid',{'isPermaLink':'false'}); g.text=guid
        ET.SubElement(item,'enclosure',{'url':enclosure,'length':str(size),'type':'audio/mpeg'})
        ET.SubElement(item,'pubDate').text=pub
        ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text=str(duration)

    for xml_name, xml_title_prefix in [
        (f'{slug}.xml', ''),
        ('prcast.xml', f'[{repo}] ')
    ]:
        x=base/'feeds'/xml_name
        tree=ET.parse(x)
        ch=tree.getroot().find('channel')
        for it in list(ch.findall('item')):
            g=it.find('guid')
            if g is not None and g.text==id_:
                ch.remove(it)
        add_item(
            ch,
            f'{xml_title_prefix}{title}',
            link,
            desc,
            id_,
            f'https://fraga.github.io/prcast/audio/{slug}/{audio_file}',
            pub_rfc,
            dur,
            size
        )
        lbd=ch.find('lastBuildDate')
        if lbd is not None:
            lbd.text=pub_rfc
        tree.write(x,encoding='UTF-8',xml_declaration=True)

    print('updated',audio_path,'dur',dur,'size',size)

if __name__ == '__main__':
    asyncio.run(main())
