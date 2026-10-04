"""Offline mock vision provider providing hilarious deterministic and randomized critiques."""

from __future__ import annotations

import random
from typing import Dict, List, Tuple
from roastbot.config import RoastSeverity, RoastCategory, MascotEmotion
from roastbot.providers.base import BaseVisionProvider, VisionAnalysisResult


ROAST_DATABASE: Dict[RoastCategory, Dict[RoastSeverity, List[Tuple[str, int, MascotEmotion, List[str], bool]]]] = {
    RoastCategory.DESK_CLUTTER: {
        RoastSeverity.GENTLE: [
            ("Your desk looks like a cozy bird nest, if the bird was an aspiring hardware hacker who lost their screwdriver.", 62, MascotEmotion.SNARKY, ["tangled cord", "paper stack", "coffee mug"], False),
            ("A delightfully lived-in workspace! I give the cable management a gentle 5 out of 10 for abstract expressionism.", 58, MascotEmotion.IDLE, ["creative cable art", "snack wrapper"], False),
        ],
        RoastSeverity.SNARKY: [
            ("Your cable management looks like an O(N!) algorithm implemented in copper wire. Did you hire a family of raccoons to wire this?", 34, MascotEmotion.SNARKY, ["wire nest", "dust bunny", "3 empty mugs"], False),
            ("I’ve seen cleaner archaeological dig sites. That sticky note from 2023 is officially historical artifact status.", 29, MascotEmotion.SNARKY, ["ancient sticky note", "crumbled paper", "microfiber cloth"], False),
        ],
        RoastSeverity.SAVAGE: [
            ("Your desk is the physical embodiment of unhandled exceptions. The CDC called, they want to quarantine that keyboard.", 15, MascotEmotion.SHOCKED, ["sticky spacebar", "moldy coffee", "cable jungle"], False),
            ("If Marie Kondo saw this workstation, she wouldn't just ask if it sparks joy—she would file a restraining order.", 12, MascotEmotion.ROASTING, ["clutter tornado", "mystery crumbs", "empty energy drink"], False),
        ],
        RoastSeverity.GORDON_RAMSAY: [
            ("WHAT IS THAT DISASTER ON THE LEFT?! IS THAT A THREE-DAY OLD ESPRESSO CUP?! YOU ARE CODING IN A PIG STY! DREADFUL!", 5, MascotEmotion.ROASTING, ["toxic biohazard mug", "cable catastrophe", "desk carnage"], False),
            ("SHUT IT DOWN! SHUT IT DOWN RIGHT NOW! LOOK AT THESE CABLES! IT'S RAW! A COMPLETE DOG'S DINNER!", 8, MascotEmotion.ROASTING, ["raw cable mess", "trash archipelago"], False),
        ],
    },
    RoastCategory.POSTURE_CHECK: {
        RoastSeverity.GENTLE: [
            ("Time to unfurl that spine, friend! You're looking a tiny bit like a gentle cashew nut right now.", 65, MascotEmotion.IDLE, ["curved spine", "relaxed shoulders"], False),
            ("A slight hunch detected! Roll those shoulders back and take a deep breath—your vertebrae will thank you.", 70, MascotEmotion.SNARKY, ["forward neck tilt", "desk lean"], False),
        ],
        RoastSeverity.SNARKY: [
            ("Your spine currently resembles the trajectory of an unoptimized CSS flexbox layout. Sit up before you calcify into a shrimp.", 38, MascotEmotion.SNARKY, ["boiled shrimp spine", "hunched shoulders"], False),
            ("Ergonomists around the globe just gasped in unison. Your neck is leaning forward at an impressive 45-degree panic angle.", 31, MascotEmotion.SHOCKED, ["tech neck", "slouching posture"], False),
        ],
        RoastSeverity.SAVAGE: [
            ("You are currently sitting like a gargoyle guarding a medieval cathedral. Your chiropractor is already booking their next yacht.", 18, MascotEmotion.SHOCKED, ["gargoyle slouch", "hollow chest", "folded legs"], False),
            ("Evolution took 6 million years to get humans to walk upright, and you reversed the entire process in four sprints.", 14, MascotEmotion.ROASTING, ["primordial posture", "extreme hunch"], False),
        ],
        RoastSeverity.GORDON_RAMSAY: [
            ("STAND UP STRAIGHT! YOU ARE BENT LIKE A BROKEN CHURRO! LOOK AT THAT SPINE! ABSOLUTELY SHOCKING!", 10, MascotEmotion.ROASTING, ["broken churro posture", "spine disaster"], False),
            ("WHAT ARE YOU SITTING ON?! A BED OF NAILS?! YOU LOOK LIKE A CRUMPLED SOUFFLE! WAKE UP!", 12, MascotEmotion.ROASTING, ["crumpled spine", "neck collapse"], False),
        ],
    },
    RoastCategory.DRIP_CHECK: {
        RoastSeverity.GENTLE: [
            ("Rocking the classic developer uniform today! The oversized hoodie is 100% comfort-engineered.", 75, MascotEmotion.IDLE, ["hoodie", "relaxed fit"], False),
            ("Looking ready for a productive sprint. Clean casual vibes with zero unnecessary corporate friction.", 78, MascotEmotion.IDLE, ["t-shirt", "headphones"], False),
        ],
        RoastSeverity.SNARKY: [
            ("The 'unwashed hackathon hoodie from 2021' aesthetic is really coming through today. High fashion for someone whose primary peer review is GitHub Actions.", 44, MascotEmotion.SNARKY, ["grey hoodie", "messy hair", "tangled headset"], False),
            ("You dressed up today like an off-duty sysadmin who just got woken up by PagerDuty at 3:14 AM.", 40, MascotEmotion.SNARKY, ["faded tech tee", "sweatpants energy"], False),
        ],
        RoastSeverity.SAVAGE: [
            ("Your wardrobe says 'I haven't committed to git or personal hygiene since Tuesday'. That shirt looks like it was ironed with a rock.", 22, MascotEmotion.ROASTING, ["wrinkled fabric", "questionable stains", "drip deficit"], False),
            ("The drip is at negative Kelvin. Even the AI upscale algorithm is refusing to render that collar properly.", 19, MascotEmotion.SHOCKED, ["fashion crisis", "disheveled dev"], False),
        ],
        RoastSeverity.GORDON_RAMSAY: [
            ("LOOK AT THAT SHIRT! IT LOOKS LIKE A DISHCLOTH FROM A SUSPECT KEBAB SHOP! HAVE SOME PRIDE IN YOURSELF!", 15, MascotEmotion.ROASTING, ["dishcloth drip", "wrinkle nightmare"], False),
            ("WHAT IS THAT ENSEMBLE?! YOU LOOK LIKE YOU ROLLED OUT OF A RECYCLING BIN! EMBARRASSING!", 11, MascotEmotion.ROASTING, ["bin couture", "chaotic collar"], False),
        ],
    },
    RoastCategory.HYDRATION_HERO: {
        RoastSeverity.GENTLE: [
            ("HURRAH! HYDRATION DETECTED! Look at you sipping that glorious H2O like a champion of cellular health!", 100, MascotEmotion.CELEBRATING, ["water vessel", "hydrated cells", "glowing skin"], True),
            ("Praise the hydration gods! Every sip is a bug solved before it happens. Keep glowing!", 95, MascotEmotion.CELEBRATING, ["refreshing water", "hydration victory"], True),
        ],
        RoastSeverity.SNARKY: [
            ("ALERT: LIQUID DETECTED THAT IS NOT 300mg OF CAFFEINE! Are you actually drinking water? The simulation must be glitching!", 98, MascotEmotion.CELEBRATING, ["pure H2O", "rare health choice"], True),
            ("Look at Mr. Hydro-Homie over here hydrating their kidneys like a functional adult! We love to see it!", 92, MascotEmotion.CELEBRATING, ["tumbler", "active drinking"], True),
        ],
        RoastSeverity.SAVAGE: [
            ("STOP THE PRESSES! The human actually remembered they are 70% water and not 100% Red Bull! A miracle on desk street!", 99, MascotEmotion.CELEBRATING, ["cold water", "hydration triumph"], True),
            ("Your liver just sent a handwritten thank-you card! Drink that water like your career depends on it!", 96, MascotEmotion.CELEBRATING, ["water bottle", "vitality boost"], True),
        ],
        RoastSeverity.GORDON_RAMSAY: [
            ("FINALLY! SOME CLEAN, FRESH WATER! NOT THAT SLUDGE! GULP IT DOWN! BRILLIANT, ABSOLUTELY STUNNING!", 100, MascotEmotion.CELEBRATING, ["glorious pure water", "chef-approved hydration"], True),
            ("YES! REFRESHING! DELICIOUS! AT LAST, SOMETHING ON THIS DESK THAT IS NOT ROTTING! PROUD OF YOU!", 97, MascotEmotion.CELEBRATING, ["fresh hydration", "crisp H2O"], True),
        ],
    },
    RoastCategory.CODE_ROAST: {
        RoastSeverity.GENTLE: [
            ("Staring deeply into the code abyss, I see! Take heart—the missing semicolon is always in the last place you look.", 68, MascotEmotion.THINKING, ["code editor", "focused gaze"], False),
            ("That frown says 'it worked on localhost but failed in production'. You've got this, keep digging!", 72, MascotEmotion.IDLE, ["terminal output", "determined dev"], False),
        ],
        RoastSeverity.SNARKY: [
            ("I can hear the uncommitted git diff crying from here. 47 files changed without tests? A bold strategy.", 35, MascotEmotion.SNARKY, ["uncommitted diff", "missing tests", "console.log spam"], False),
            ("That terminal is glowing redder than Rudolph's nose. Have you tried turning the stack overflow answer off and on again?", 28, MascotEmotion.SNARKY, ["red error trace", "stack trace panic"], False),
        ],
        RoastSeverity.SAVAGE: [
            ("Your codebase is a house of cards held together by prayers and copy-pasted StackOverflow snippets from 2014.", 16, MascotEmotion.ROASTING, ["spaghetti code", "segfault vibe", "panic scroll"], False),
            ("I’ve seen cleaner architecture in a collapsed Jenga tower. Even CoPilot just muted itself in embarrassment.", 12, MascotEmotion.SHOCKED, ["architectural catastrophe", "12 nested if statements"], False),
        ],
        RoastSeverity.GORDON_RAMSAY: [
            ("THIS CODE IS RAW! IT'S CRASHING BEFORE COMPILATION! WHO WROTE THIS? AN IDIOT SANDWICH?! WAKE UP!", 6, MascotEmotion.ROASTING, ["raw uncompiled mess", "memory leak crisis"], False),
            ("HOW CAN YOU CALL YOURSELF A DEVELOPER WITH AN ERROR LOG THIS DISASTROUS?! UNACCEPTABLE!", 8, MascotEmotion.ROASTING, ["syntax catastrophe", "fatal crash"], False),
        ],
    },
    RoastCategory.CAFFEINE_RADAR: {
        RoastSeverity.GENTLE: [
            ("Coffee companion spotted! Just make sure that brew doesn't turn cold while you debug.", 70, MascotEmotion.IDLE, ["coffee cup", "steam"], False),
            ("A sensible amount of fuel for the brain engine. Sip gently and conquer those tickets!", 75, MascotEmotion.IDLE, ["warm mug", "caffeine power"], False),
        ],
        RoastSeverity.SNARKY: [
            ("You have enough empty coffee cups on that desk to construct a functional scale model of Stonehenge.", 32, MascotEmotion.SNARKY, ["mug graveyard", "cold brew can", "caffeine tremor"], False),
            ("At this point your blood type is officially Espresso Positive. Your resting heart rate sounds like a drum solo.", 26, MascotEmotion.SNARKY, ["trio of mugs", "energy drink cans"], False),
        ],
        RoastSeverity.SAVAGE: [
            ("There is enough caffeine in your bloodstream right now to vibrate you into a parallel dimension. Drink some water, you goblin.", 14, MascotEmotion.ROASTING, ["caffeine overdose", "jitter hands", "5 empty mugs"], False),
            ("That ceramic mug contains liquid that hasn't seen fresh brew since the last lunar eclipse. Don't drink that, it has formed sentience.", 10, MascotEmotion.SHOCKED, ["ancient cold sludge", "caffeine hazmat"], False),
        ],
        RoastSeverity.GORDON_RAMSAY: [
            ("LOOK AT THAT COFFEE MUG! IT'S CONGEALED! A PETRI DISH ON YOUR DESK! DISGUSTING! THROW IT IN THE BIN!", 4, MascotEmotion.ROASTING, ["congealed coffee", "biohazard desk"], False),
            ("THREE COFFEE CUPS?! THREE?! ARE YOU TRYING TO RUN A STEAM ENGINE?! GET SOME FRESH WATER IN THERE!", 9, MascotEmotion.ROASTING, ["caffeine madness", "dirty cups"], False),
        ],
    },
    RoastCategory.GENERAL_ROAST: {
        RoastSeverity.GENTLE: [
            ("All systems operational! You're in the zone today—just remember to blink occasionally.", 80, MascotEmotion.IDLE, ["focused engineer", "calm workspace"], False),
            ("Bytey reports: overall vibe is solid, brain cells firing at nominal efficiency.", 82, MascotEmotion.IDLE, ["working posture", "workspace"], False),
        ],
        RoastSeverity.SNARKY: [
            ("The facial expression of someone who just realized their 2-hour bug was a missing comma. Stay strong.", 45, MascotEmotion.SNARKY, ["thousand-yard stare", "debugging trance"], False),
            ("Looking at this whole setup, I’d rate your work-life balance at approximately 300 baud dial-up speed.", 42, MascotEmotion.SNARKY, ["dual monitor glare", "fatigued posture"], False),
        ],
        RoastSeverity.SAVAGE: [
            ("I was created by neural networks trained on the sum total of human knowledge, and I am still bewildered by this scene.", 20, MascotEmotion.SHOCKED, ["chaos aura", "existential dread"], False),
            ("Your desk looks like an escape room where the only puzzle is trying to find where your motivation went.", 15, MascotEmotion.ROASTING, ["disarray", "keyboard warrior"], False),
        ],
        RoastSeverity.GORDON_RAMSAY: [
            ("MY GRANDMOTHER COULD WRITE CLEANER CODE AND HER COMPUTER WAS A TOASTER! GET A GRIP!", 8, MascotEmotion.ROASTING, ["complete disaster", "amateur hour"], False),
            ("LOOK AT THIS ENTIRE SCENE! NO PLAN, NO DISCIPLINE, JUST PURE UNADULTERATED MADNESS! APPALLING!", 6, MascotEmotion.ROASTING, ["unadulterated chaos", "kitchen nightmare desk"], False),
        ],
    },
}


class MockVisionProvider(BaseVisionProvider):
    """Deterministic, hilarious offline vision provider requiring zero API keys."""

    name: str = "mock"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    async def analyze_frame(
        self,
        frame_bytes: bytes,
        severity: RoastSeverity,
        category: RoastCategory,
    ) -> VisionAnalysisResult:
        """Select a humorous roast matching the category and severity."""
        category_roasts = ROAST_DATABASE.get(category, ROAST_DATABASE[RoastCategory.GENERAL_ROAST])
        severity_roasts = category_roasts.get(severity, category_roasts[RoastSeverity.SNARKY])

        # Pick one item from the curated bank
        choice = self.rng.choice(severity_roasts)
        roast_text, score, emotion, items, is_celeb = choice

        return VisionAnalysisResult(
            roast=roast_text,
            score=score,
            emotion=emotion,
            category=category,
            severity=severity,
            detected_items=items.copy(),
            is_celebration=is_celeb,
            provider_name="mock",
            raw_response=f'{{"mock": true, "category": "{category.value}", "severity": "{severity.value}"}}'
        )
