#!/usr/bin/env python3
"""Install actual third-party narrative skills inside the two project subtrees.

No repository code is executed. Archives are downloaded and relevant files are copied.
Run: python Tools/install_real_narrative_skills.py
Requires: Python 3.10+, internet. No pip dependencies.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / 'design-doc'
LORE = VAULT / '02. Мир и лор' / '.claude' / 'skills'
STORY = VAULT / '04. Сюжет и повествование' / '.claude' / 'skills'
LORE.parent.mkdir(parents=True, exist_ok=True)
STORY.parent.mkdir(parents=True, exist_ok=True)
MAX_DOWNLOAD = 175 * 1024 * 1024
MAX_FILE = 18 * 1024 * 1024
REPOS = {
    'fcsouza': ('fcsouza', 'agent-skills', 'main'),
    'jwynia': ('jwynia', 'agent-skills', 'main'),
    'alterlab': ('AlterLab-IEU', 'AlterLab_GameForge', 'main'),
    'story-skills': ('danjdewhurst', 'story-skills', 'main'),
    'narrative-upstream': ('poorvith-mp', 'skills-gamedev', 'main'),
}


def fetch(url: str) -> bytes:
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'GameProject-SkillInstaller/1.0', 'Accept':'application/octet-stream'})
            with urllib.request.urlopen(req, timeout=75) as response:
                chunks, size = [], 0
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk: break
                    size += len(chunk)
                    if size > MAX_DOWNLOAD: raise RuntimeError(f'Archive too large: {url}')
                    chunks.append(chunk)
            return b''.join(chunks)
        except Exception as exc:
            last = exc
            if attempt < 2: time.sleep(2 + attempt * 2)
    raise RuntimeError(f'Cannot download {url}: {last}')


def fetch_repo(name: str) -> tuple[zipfile.ZipFile, str, str]:
    owner, repo, branch = REPOS[name]
    url = f'https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}'
    raw = fetch(url)
    zf = zipfile.ZipFile(io.BytesIO(raw))
    return zf, hashlib.sha256(raw).hexdigest(), url


def safe_files(zf: zipfile.ZipFile, prefix: str):
    """Get entries under a repo-relative prefix; block traversal and zip symlinks."""
    root = zf.namelist()[0].split('/')[0] + '/'
    full_prefix = root + prefix.strip('/') + '/'
    for member in zf.infolist():
        if member.is_dir() or not member.filename.startswith(full_prefix): continue
        rest = member.filename[len(full_prefix):]
        parts = Path(rest).parts
        if not parts or any(x in ('..', '') for x in parts): continue
        if member.file_size > MAX_FILE:
            raise RuntimeError(f'Oversize file in downloaded skill: {member.filename}')
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise RuntimeError(f'Unsafe symlink in archive: {member.filename}')
        yield member, Path(*parts)


def copy_subtree(zf: zipfile.ZipFile, prefix: str, dest: Path, *, required=True):
    copied = 0
    for member, relative in safe_files(zf, prefix):
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(zf.read(member))
        copied += 1
    if required and not copied:
        raise RuntimeError(f'Missing directory in repository archive: {prefix}')
    return copied


def copy_one(zf: zipfile.ZipFile, repository_path: str, destination: Path, *, optional=False):
    repo_root = zf.namelist()[0].split('/')[0] + '/'
    key = repo_root + repository_path.strip('/')
    try: data = zf.read(key)
    except KeyError:
        if optional: return False
        raise RuntimeError(f'Missing required source file: {repository_path}')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return True


def stage_skill_path(stage: Path, area: str, name: str):
    path = stage / area / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def replace_skill_name(path: Path, old: str, new: str):
    skill_file = path / 'SKILL.md'
    original = skill_file.read_text(encoding='utf-8')
    (path / 'SKILL.upstream.md').write_text(original, encoding='utf-8')
    replaced = re.sub(r'^name:\s*' + re.escape(old) + r'\s*$', 'name: ' + new, original, count=1, flags=re.MULTILINE)
    if replaced == original: raise RuntimeError(f'Cannot rename skill in YAML: {skill_file}')
    skill_file.write_text(replaced, encoding='utf-8')


def add_licenses(zf, dest: Path, src='LICENSE'):
    copy_one(zf, src, dest / 'LICENSE', optional=True)


def stage_all(stage: Path):
    records = []
    # 1. fcsouza: original worldbuilding and required quest-narrative-coherence with templates.
    print('  [1/5] Narrative Worldbuilding (+ quest-narrative-coherence)')
    zf, digest, url = fetch_repo('fcsouza')
    for src,name in [('skills/worldbuilding','narrative-worldbuilding'), ('skills/quest-narrative-coherence','quest-narrative-coherence')]:
        dest = stage_skill_path(stage, 'lore', name)
        copy_subtree(zf, src, dest)
        if not (dest/'SKILL.md').is_file():raise RuntimeError('Missing SKILL.md in '+name)
        add_licenses(zf,dest)
    records.append({'source':'fcsouza/agent-skills', 'download':url, 'sha256_archive':digest, 'skills':['narrative-worldbuilding','quest-narrative-coherence']})
    zf.close()

    # 2. jwynia: original diagnostic; only the YAML name is changed to avoid clashing with story-skills.
    print('  [2/5] Worldbuilding Diagnostic')
    zf,digest,url=fetch_repo('jwynia')
    dest=stage_skill_path(stage,'lore','worldbuilding-diagnostic')
    copy_subtree(zf,'skills/creative/fiction/worldbuilding/worldbuilding',dest)
    replace_skill_name(dest,'worldbuilding','worldbuilding-diagnostic')
    add_licenses(zf,dest)  # Optional: source declares MIT in SKILL.md.
    records.append({'source':'jwynia/agent-skills', 'download':url,'sha256_archive':digest,'skills':['worldbuilding-diagnostic'],'adaptation':'only frontmatter name; original retained as SKILL.upstream.md'})
    zf.close()

    # 3. GameSkill tuned build; falls back to fully attributed upstream only when unavailable.
    print('  [3/5] Narrative Design (GameSkill tested build)')
    dest=stage_skill_path(stage,'story','narrative-design')
    gs_url='https://gameskill.dev/dl/skills/narrative-design.zip'
    gs_status='GameSkill tuned'
    try:
        gs_raw=fetch(gs_url)
        gs=zipfile.ZipFile(io.BytesIO(gs_raw))
        members=[m for m in gs.infolist() if not m.is_dir()]
        possible=[m.filename for m in members if m.filename.endswith('SKILL.md') and ('narrative-design' in m.filename or m.filename=='SKILL.md')]
        if not possible: raise RuntimeError('Downloaded GameSkill zip does not contain a narrative-design SKILL.md')
        skillpath=min(possible, key=len)
        base=skillpath[:-len('SKILL.md')]
        for m in members:
            if not m.filename.startswith(base): continue
            rel=m.filename[len(base):]
            if not rel or '..' in Path(rel).parts or m.file_size>MAX_FILE: continue
            p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(gs.read(m))
        if not (dest/'SKILL.md').is_file():raise RuntimeError('Narrative Design SKILL.md absent after extraction')
        digest=hashlib.sha256(gs_raw).hexdigest()
        source=gs_url
    except Exception as e:
        print('      GameSkill download unavailable; using original MIT upstream:',str(e)[:140])
        gs_status='upstream fallback (not GameSkill tested build)'
        zf,digest,source=fetch_repo('narrative-upstream')
        copy_subtree(zf,'skills/narrative-design',dest)
        add_licenses(zf,dest)
        zf.close()
    records.append({'source':'gameskill.dev/skills/narrative-design','download':source,'sha256_archive':digest,'skills':['narrative-design'],'variant':gs_status})

    # 4. GameForge director and supporting references, with link-path fixes.
    print('  [4/5] Game Narrative Director (with dependencies)')
    zf,digest,url=fetch_repo('alterlab')
    dest=stage_skill_path(stage,'story','game-narrative-director')
    copy_subtree(zf,'skills/agents/game-narrative-director',dest)
    dependency_files=[
       'docs/game-design-theory.md',
       'genre-packs/narrative/PATTERNS.md',
       'templates/character-sheet.md',
       'templates/ai-asset-log.md',
    ]
    for rel in dependency_files: copy_one(zf,rel,dest/'references'/'gameforge-upstream'/rel)
    skill_file=dest/'SKILL.md'
    skill_text=skill_file.read_text(encoding='utf8')
    (dest/'SKILL.upstream.md').write_text(skill_text,encoding='utf8')
    for rel in dependency_files:
        skill_text=skill_text.replace('${CLAUDE_PLUGIN_ROOT}/'+rel, '${CLAUDE_SKILL_DIR}/references/gameforge-upstream/'+rel)
    skill_file.write_text(skill_text,encoding='utf8')
    add_licenses(zf,dest)
    records.append({'source':'AlterLab-IEU/AlterLab_GameForge','download':url,'sha256_archive':digest,'skills':['game-narrative-director'],'adaptation':'plugin-root references replaced by local skill reference paths; SKILL.upstream.md retains original'})
    zf.close()

    # 5. Story Skills: ALL skills/, including each references/ subtree. Do not run story CLI.
    print('  [5/5] Story Skills (complete skills directory)')
    zf,digest,url=fetch_repo('story-skills')
    story_dest=stage/'story'
    copy_subtree(zf,'skills',story_dest)
    found=sorted(p.name for p in story_dest.iterdir() if p.is_dir() and (p/'SKILL.md').is_file())
    if len(found)<20: raise RuntimeError(f'Story Skills incomplete; only {len(found)} skills found')
    license_dir=stage/'licenses'
    copy_one(zf,'LICENSE',license_dir/'story-skills-MIT-LICENSE')
    # Story Skills often references project-specific CLI and schema: keep docs for voluntary integration.
    for src in ['README.md','docs/getting-started.md','docs/project-format.md','docs/cli-reference.md','schemas/story.schema.json']:
        copy_one(zf,src,stage/'documentation'/'story-skills'/src,optional=True)
    records.append({'source':'danjdewhurst/story-skills','download':url,'sha256_archive':digest,'skills':found, 'note':'Full skill directory; optional story CLI and project schema are not installed into the game'})
    zf.close()
    return records


def install(stage: Path, records):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=ROOT/'Backups'/'Скиллы'/stamp
    changes=[]
    for area,target_root in [('lore',LORE),('story',STORY)]:
        target_root.mkdir(parents=True,exist_ok=True)
        for folder in (stage/area).iterdir():
            if not folder.is_dir():continue
            dest=target_root/folder.name
            if dest.exists():
                b=backup/area/folder.name
                b.parent.mkdir(parents=True,exist_ok=True)
                shutil.move(str(dest),str(b))
            shutil.move(str(folder),str(dest))
            changes.append(str(dest.relative_to(ROOT)))
    license_dest=ROOT/'ThirdPartyLicenses'
    license_dest.mkdir(exist_ok=True)
    for file in (stage/'licenses').glob('*'):
        shutil.copy2(file,license_dest/file.name)
    docs_src=stage/'documentation'
    if docs_src.exists():
        docs_dest=ROOT/'ThirdPartyDocs'
        shutil.copytree(docs_src,docs_dest,dirs_exist_ok=True)
    report=ROOT/'НАВЫКИ_УСТАНОВЛЕНЫ.md'
    report.write_text('# Установленные сторонние скиллы\n\n'
       'Дата (UTC): '+stamp+'\n\n'
       'Установлены **оригинальные материалы**, загруженные из указанных источников; см. архивные SHA256 ниже.\n'
       'Путь применения: `02. Мир и лор` или `04. Сюжет и повествование`; Unity не затронут.\n\n'
       '```json\n'+json.dumps(records,ensure_ascii=False,indent=2)+'\n```\n\n'
       'Файлы из сторонних репозиториев рассматриваются как недоверенные: код из них автоматически не выполнялся.\n'
       'Скиллы не являются техническими границами доступа и могут оставаться активными до конца сессии Claude.\n',encoding='utf8')
    return changes,backup


def main():
    if not (VAULT/'.obsidian').exists():
        print('ERROR: run this script inside unpacked GameProject with Obsidian vault',file=sys.stderr);return 1
    print('Installing original third-party narrative skills into',ROOT)
    print('No repository script will be executed. Internet required.\n')
    try:
        with tempfile.TemporaryDirectory(prefix='narrative_skills_') as tmp:
            stage=Path(tmp)
            for d in ['lore','story','licenses','documentation']: (stage/d).mkdir()
            records=stage_all(stage)
            changes,backup=install(stage,records)
    except Exception as exc:
        print('\nInstallation stopped:',str(exc),file=sys.stderr)
        print('No source code was executed. Check Internet access and retry.',file=sys.stderr)
        return 1
    print('\nInstalled',len(changes),'skill folders. Backup (if needed):',backup)
    print('Complete manifest: НАВЫКИ_УСТАНОВЛЕНЫ.md')
    print('Restart Claude Code and launch from the appropriate subtree.')
    return 0


if __name__=='__main__':
    sys.exit(main())
