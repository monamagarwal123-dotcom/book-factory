
"""
Story Writer Agent - Writes children's book chapters
Now per-book project: each book has its own folder
"""
import json
from pathlib import Path
from core.book_bible import BookBible
from core.llm_router import llm_router
from core.filenames import format_chapter_id, format_chapter_filename, format_chapter_meta_filename, format_outline_filename

class StoryWriter:
    def __init__(self, project_id=None):
        self.project_id = project_id
        # Get project-aware bible
        self.bible = BookBible(project_id=project_id)
        self.router = llm_router
        # Ensure chapters dir for this project
        try:
            from core.project_manager import project_manager
            chapters_dir = project_manager.get_chapters_dir(project_id)
            chapters_dir.mkdir(parents=True, exist_ok=True)
        except:
            Path("book_data/chapters").mkdir(parents=True, exist_ok=True)
            chapters_dir = Path("book_data/chapters")
        self.chapters_dir = chapters_dir
    
    def get_bible_context(self):
        data = self.bible.data
        ctx = f"""
BOOK BIBLE:
Title: {data.get('title', 'Untitled')}
Author: {data.get('author', 'Unknown')}
Audience: {data.get('audience', 'children ages 4-8')}
Art Style: {data.get('art_style', 'soft watercolor')}
Tone: {data.get('style_guide', {}).get('tone', 'warm, curious')}

CHARACTERS:
"""
        for name, char in data.get('characters', {}).items():
            ctx += f"- {name}: {char.get('description', '')} (outfit: {char.get('outfit', '')})\n"
        ctx += f"""
STYLE GUIDE:
- Sentence length: {data.get('style_guide', {}).get('sentence_length', 'short')}
- Tone: {data.get('style_guide', {}).get('tone', 'warm')}
- No scary content, positive, curious
"""
        return ctx
    
    def write_chapter(self, chapter_id, prompt, word_count=300, age_group="4-8"):
        formatted_id = format_chapter_id(chapter_id)
        bible_ctx = self.get_bible_context()
        
        # Load previous chapters from THIS book only - SKIP placeholders
        prev_chapters = ""
        count = 0
        for f in sorted(self.chapters_dir.glob("ch*.txt")):
            if f.stem == formatted_id:
                continue
            if count >= 3:  # Only last 3 good chapters
                break
            try:
                content = f.read_text()
                # Skip if it's a placeholder/failure
                if "[Placeholder" in content or "Write chapter ch" in content[:100] or len(content) < 80:
                    print(f"[StoryWriter] Skipping placeholder {f.stem}")
                    continue
                # Clean content for continuity - only first 400 chars of actual story
                clean = content[:400].replace("Write chapter", "").replace("Chapter prompt:", "")[:400]
                prev_chapters += f"\n--- {f.stem} ---\n{clean}..."
                count += 1
            except:
                pass
        
        system_prompt = f"""You are a children's book author for ages {age_group}.
{bible_ctx}

RULES:
- Write warm, curious, positive stories
- Short sentences, simple words
- Keep characters consistent (same outfit, hair, etc)
- {word_count} words target
- No scary, no violence
- End with gentle cliffhanger or lesson
- Format: Title on first line, then story paragraphs
"""
        user_prompt = f"""Write chapter {formatted_id}:

Chapter prompt: {prompt}

Previous chapters for continuity:
{prev_chapters if prev_chapters else "This is the first chapter."}

Write {word_count} words. Keep {self.bible.data.get('characters', {}).keys()} consistent.
"""
        print(f"[StoryWriter] Writing {chapter_id} -> formatted '{formatted_id}' in project {self.project_id or 'legacy'} with {self.router.model_key}: {prompt[:60]}...")
        story = self.router.generate(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=word_count * 2,
            temperature=0.8
        )
        out_path = format_chapter_filename(formatted_id, project_id=self.project_id)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(story)
        
        meta_path = format_chapter_meta_filename(formatted_id, project_id=self.project_id)
        meta = {
            "id": formatted_id,
            "original_id": chapter_id,
            "prompt": prompt,
            "word_count": len(story.split()),
            "model": self.router.model_key,
            "file": str(out_path),
            "project_id": self.project_id
        }
        meta_path.write_text(json.dumps(meta, indent=2))
        
        print(f"[StoryWriter] ✅ Wrote {chapter_id} -> '{formatted_id}' -> {out_path} ({len(story.split())} words)")
        return story, out_path
    
    def write_outline(self, num_chapters=5, premise="Sarah's adventure"):
        bible_ctx = self.get_bible_context()
        system_prompt = f"""You are a children's book outline writer.
{bible_ctx}

Create a {num_chapters}-chapter outline for a children's book.
Each chapter: 1-2 sentence summary, with emotional arc.
"""
        user_prompt = f"""Premise: {premise}
Create {num_chapters} chapter outlines. Format:
1. Chapter title: summary
2. ...
"""
        print(f"[StoryWriter] Generating outline with {self.router.model_key} for project {self.project_id}...")
        outline = self.router.generate(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=1000,
            temperature=0.7
        )
        out_path = format_outline_filename(project_id=self.project_id)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(outline)
        print(f"[StoryWriter] ✅ Outline -> {out_path}")
        return outline
