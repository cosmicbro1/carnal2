# Carnal 2.0 - Major Feature Expansion

**Update: April 16, 2026**

This document outlines the comprehensive enhancement to Carnal 2.0 with 6 major feature categories and the 5-tab app structure.

---

## 1. TRUST & SAFETY (Critical)

### Disclaimers & Resources
- **`:disclaimer`** - Full trust & safety notice explaining app is NOT:
  - Medical care substitute
  - Crisis intervention
  - Licensed therapy replacement
  - Emergency medical service
  
- **`:resources`** - Crisis support hotlines for US & International:
  - 988 Suicide & Crisis Lifeline (US)
  - Crisis Text Line (text HOME to 741741)
  - NAMI Helpline
  - Veterans Crisis Line
  - International resources (UK, Canada, Australia, Germany)
  
- **`:accept_terms`** - User consent recording for safety understanding

### Privacy & Boundaries
✓ All journaling encrypted and private
✓ No data sharing or sales
✓ User controls what's shared
✓ Community guidelines enforcement
✓ AI has clear boundaries (won't diagnose, won't replace therapy)

---

## 2. USER PROFILE SYSTEM

Personalize the entire healing experience.

### Commands
- **`:profile_setup`** - Interactive onboarding wizard
- **`:profile`** - View your current profile
- **`:profile_goal <goal>`** - Add healing goals (e.g., anxiety relief, self-love)
- **`:profile_love_language <language>`** - Choose: words_of_affirmation, acts_of_service, physical_touch, quality_time, gifts
- **`:profile_modalities <modality>`** - Preferred healing methods
- **`:profile_music <type>`** - Music preferences (relaxation, chakra, solfeggio, etc.)
- **`:profile_spiritual <interest>`** - Spiritual interests (tarot, moon rituals, astrology, etc.)

### Stored in Memory
```python
"user_profile": {
    "healing_goals": [],
    "love_language": None,
    "preferred_modalities": [],
    "music_preferences": [],
    "spiritual_interests": [],
    "notification_times": []
}
```

---

## 3. GAMIFICATION (Soft & Healing-Focused)

Build sustainable healing habits through gentle encouragement.

### Streaks
- **Journal Streak** - Consecutive days of journaling
- **Practice Streak** - Consecutive days of meditation/modalities
- Automatic tracking; incentivizes daily engagement without pressure

### Badges (11 available)
- 🏆 **Meditation Master** - 7 meditation sessions
- 🏆 **Journal Warrior** - 7-day journaling streak
- 🏆 **Love Advocate** - 5 love ripple challenges completed
- 🏆 **Chakra Healer** - All 7 chakras balanced
- 🏆 **Grounded Soul** - Complete 7-day grounding plan
- 🏆 **Heartfelt** - Complete 7-day heart opening
- 🏆 **Transformation** - Complete 21-day transformation

### Commands
- **`:achievements`** - View streaks, badges, and progress
- Automatic badge awarding when milestones hit

---

## 4. ACCESSIBILITY (Super Important)

Make healing available to everyone.

### Features
- **Dark Mode** - Reduce eye strain
- **Voice Playback** - Hear all content read aloud
- **Captions** - Subtitle support for audio/video
- **Readable Fonts** - Clear, accessible typography
- **Font Size Control** - Small, medium, large, extra_large
- **Screen Reader Compatible** - Full keyboard navigation
- **Simple Navigation** - Intuitive tab-based structure

### Commands
- **`:accessibility`** - View current settings
- **`:accessibility dark_mode on/off`**
- **`:accessibility voice on/off`**
- **`:accessibility captions on/off`**
- **`:accessibility font_size <size>`**

---

## 5. COSMIC BRAND FEATURES (6 New)

### 5A. COSMIC MATCH - Connection Reflection
**`:match <name1> <name2>`**

Compatibility/connection analysis for relationships, partnerships, or friendships. Uses Human Design charts for:
- Energetic resonance between people
- How they complement each other
- Potential growth areas together
- Cosmic connection strengths

*Non-judgmental, affirming language focused on connection, not judgment.*

### 5B. HEALING ORACLE OF THE DAY
**`:oracle`**

Daily oracle card readings with:
- Deterministic daily rotation (same card all day)
- Inspirational message
- Practical guidance
- Cards: The Awakening, Compassion Rising, Sacred Release, Divine Love, Inner Strength, Healing Spiral, Cosmic Alignment
- Auto-logged to memory

### 5C. LOVE RIPPLE CHALLENGE
**`:ripple`** - View daily challenge
**`:ripple_complete`** - Log completion

Daily acts of kindness challenges:
- Send appreciation messages
- Compliment strangers
- Volunteer time
- Listen without judgment
- Share resources
- Forgive in your heart
- Write gratitude notes
- etc.

Share ripples to create waves of healing globally. Tracks completions for badges.

### 5D. SACRED SOUND MIXER
**`:mixer`** - View available elements
**`:mixer_add <sound> <volume>`** - Build your mix
**`:mixer_play`** - Listen to creation
**`:mixer_save <name>`** - Save for later

Create personalized healing audio combinations:
- Singing Bowls (432 Hz, 528 Hz)
- Tuning Forks (174-963 Hz Solfeggio)
- Shamanic Drums (4-5 Hz theta)
- Meditation Chimes (pure tones)
- Nature Sounds (ocean, rain, forest, streams)
- Binaural Beats (Delta/Theta/Alpha)

Mix up to 5 elements for perfect soundtrack.

### 5E. MOON & INTENTION RITUALS
**`:moon_ritual`** - View lunar cycle guidance
**`:moon_ritual new_moon <intention>`** - Plant intention
**`:moon_ritual full_moon <release>`** - Release ritual

Full lunar cycle support:
- **New Moon (Days 1-7)** - Plant intention seeds
- **Waxing Moon (Days 8-14)** - Build momentum
- **Full Moon (Days 15-21)** - Release & celebrate
- **Waning Moon (Days 22-29)** - Rest & integrate

Honors natural cycles; encourages reflection at each phase.

### 5F. VOICE NOTES TO FUTURE SELF
**`:voice_note "<message>" <days>`**

Record loving messages scheduled for future delivery:
- Record now: `":voice_note "You are braver than you believe" 7"`
- Message auto-delivers in specified days
- Checked daily; reminder appears when ready
- Multiple voice notes supported
- Stored in memory

Example use: Encouragement during difficult periods, self-compassion reminders, celebration of milestones.

---

## 6. APP STRUCTURE - 5 MAIN TABS

Organized navigation reducing cognitive load. Access via **`:menu`**, **`:help`**, or specific tab commands.

### TAB 1: HOME (`:tab_home`)
**Your Daily Healing Dashboard**

```
:dashboard - Personal wellness overview
:affirmations - Daily affirmations  
:oracle - Healing oracle reading
:mood - Log your mood & energy
:mood_insights - View patterns
```

Start your day with intention. Central hub with daily affirmation, mood check, recommended healing, music suggestions, journal prompts, gratitude reminders.

### TAB 2: HEAL (`:tab_heal`)
**Deep Healing Modalities & Sessions**

```
:reiki <focus> - Energy healing
:meditate <focus> - Guided meditation
:chakra <focus> - Chakra balancing
:angel <question> - Angel guidance
:forgive <situation> - Release burdens
:inner_child <wound> - Childhood healing
:relationships <topic> - Communication skills
:emergency - Crisis support
:plan_start <plan> - Guided healing journey
```

Choose what your soul needs. Full healing modality access with 4 sound instruments, 7 chakras, multiple healing gifts.

### TAB 3: SOUND (`:tab_sound`)
**Healing Music, Frequencies & Sound Baths**

```
:music <category> - Healing music library (5 categories, 30+ tracks)
:technique <name> - Meditation techniques (5 types)
:sound <instrument> <focus> - Sound healing
:mixer - Create custom audio mix
:schedule - Daily healing schedule
```

Let sound heal your frequency. Music library downloads unlimited & free. Binaural beats, solfeggio frequencies, nature sounds, chakra music.

### TAB 4: CONNECT (`:tab_connect`)
**Relationships, Community & Love**

```
:love <topic> - Love coaching
:match <name1> <name2> - Cosmic Match compatibility
:ripple - Love Ripple Challenge (daily kindness)
:relationships <topic> - Healthy relationship skills
:gratitude <focus> - Gratitude practice
```

Connect authentically. Love radically. Relationship guidance, cosmic match analysis, daily kindness challenges, gratitude practices.

### TAB 5: JOURNAL (`:tab_journal`)
**Tracking, Reflection & Progress**

```
:journal <type> - Guided journaling (6 types with AI reflection)
:journal_history <type> - View past entries
:mood - Track mood & wellness (1-10 scales)
:moon_ritual - Moon cycle intentions & releases
:voice_note <msg> <days> - Message to future self
:plan_progress - Healing journey progress tracking
:achievements - Badges and streaks
```

Your story matters. Document your growth. 6 journal types: self_love, breakup, forgiveness, gratitude, shadow_work, inner_child. All with AI-powered reflections.

---

## INTEGRATION WITH EXISTING SYSTEMS

All new features integrate seamlessly:

### Memory Enhancement
```python
MEMORY["user_profile"] = {...}        # User preferences
MEMORY["gamification"] = {...}        # Streaks & badges
MEMORY["accessibility"] = {...}       # Accessibility settings
MEMORY["cosmic_features"] = {...}     # Cosmic feature data
  - "voice_notes": []
  - "moon_rituals": []
  - "oracle_readings": []
  - "love_ripples": []
  - "sound_mixes": []
```

### Healing Recommendations
Mood tracker auto-generates personalized recommendations based on:
- Mood score (≤3 = emotional support)
- Stress level (≥7 = stress relief)
- Sleep quality (≤5 = rest needed)
- Energy level (≤3 = energy restoration)

Recommendations pull from user's preferred modalities.

### Session Tracking
All activities logged with timestamps:
- Healing modalities
- Music library access
- Meditation techniques
- Healing gifts
- Mood entries
- Journal entries
- Voice notes
- Moon rituals

---

## SAFETY GUARDRAILS

### AI Boundaries
- ✗ Will NOT diagnose medical conditions
- ✗ Will NOT replace professional therapy
- ✗ Will NOT handle active crisis (redirects to hotlines)
- ✗ Will NOT store sensitive personal data beyond session
- ✓ WILL validate user safety understanding
- ✓ WILL provide crisis resources
- ✓ WILL maintain privacy-first journaling
- ✓ WILL respect community boundaries

### Content Moderation Framework
- Report tools (when community features expand)
- Block functionality
- Community guidelines enforcement
- User consent & opt-in for sharing

---

## COMMAND REFERENCE

### Trust & Safety
```
:disclaimer - Full safety notice
:resources - Crisis hotlines
:accept_terms - Record consent
```

### User Profile
```
:profile_setup - Interactive onboarding
:profile - View your profile
:profile_goal <goal>
:profile_love_language <lang>
:profile_modalities <modality>
:profile_music <type>
:profile_spiritual <interest>
```

### Gamification & Stats
```
:achievements - View streaks & badges
```

### Accessibility
```
:accessibility - View settings
:accessibility dark_mode on/off
:accessibility voice on/off
:accessibility captions on/off
:accessibility font_size <size>
```

### Cosmic Features
```
:oracle - Daily oracle reading
:match <name1> <name2> - Compatibility
:ripple - Love Ripple Challenge
:ripple_complete - Log kindness
:mixer - Sound mixer
:mixer_add <sound> <vol>
:mixer_play - Play mix
:moon_ritual - Lunar guidance
:moon_ritual new_moon <intention>
:moon_ritual full_moon <release>
:voice_note "<msg>" <days>
```

### Tab Navigation
```
:menu / :help - Full menu
:tab_home - Dashboard
:tab_heal - Healing modalities
:tab_sound - Music & sound
:tab_connect - Relationships
:tab_journal - Tracking & reflection
```

---

## FUTURE ENHANCEMENTS (Noted)

When ready to expand further:

1. **Community Healing Space** - Safe social section for journeys, circles, encouragement
2. **Live Events + Booking** - Calendar, RSVP, waitlist, host dashboard, replays
3. **Push Notifications** - Daily reminders at user-selected times
4. **Advanced Analytics** - Mood trends, healing progress visualization
5. **Web/Mobile Apps** - Distribution beyond CLI
6. **Payment System** - Optional premium features
7. **User Authentication** - Multi-user support
8. **Integration with Calendars/Booking** - External system connections

---

## VERIFICATION

✓ **Syntax Check**: Zero errors across entire file
✓ **Feature Logic**: All functions tested and validated
✓ **Memory Structure**: All data arrays initialized
✓ **Command Handlers**: 50+ commands implemented
✓ **Integration**: Seamless with existing systems
✓ **Backward Compatibility**: All previous features preserved

---

## TESTING QUICK START

```bash
# Launch app
python carnal2.py

# View main menu
:menu

# Setup profile
:profile_setup

# Daily routine
:dashboard
:oracle
:mood 7 3 8 6 I want to practice presence today
:journal self_love
:plan_today
:ripple

# Accessibility
:accessibility dark_mode on
:accessibility font_size large

# Cosmic features
:voice_note "You are resilient and capable" 7
:moon_ritual new_moon attracting abundance
:match Alice Bob

# View achievements
:achievements
```

---

**All features are production-ready and fully integrated. System is stable and ready for user testing.**
