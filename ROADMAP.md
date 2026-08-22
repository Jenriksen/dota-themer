# Dota Themer - Project Roadmap

## Overview

**Dota Themer** is a tool that makes hero selection challenging and fun by suggesting themes and listing matching heroes with their viable positions. This roadmap outlines the strategic direction, key milestones, and release phases for the project.

---

## Vision & Goals

### Core Value Proposition
- Provide Dota 2 players with creative constraints for hero selection
- Enable coordinated team composition through thematic hero picking
- Support both casual play and organized party queues

### Success Metrics
- [ ] 8+ themes available (Current: 8 ✅)
- [ ] 100+ heroes with accurate position data (Current: 108 ✅)
- [ ] Discord bot deployed and active in at least one server
- [ ] 72+ unit tests passing (Current: 86+ ✅)
- [ ] Regular usage by 50+ unique users/month (Future target)

---

## Current Status (as of Latest Commit)

### ✅ Completed
- Domain modeling complete (CONTEXT.md)
- Core logic implemented (core.py)
- Data infrastructure: 108 heroes, 8 themes
- Comprehensive test suite: 86+ unit tests
- Discord bot integration (bot.py)
- Position-based features: lane grouping, balanced suggestions
- Enhanced theme selection: filtering, weighting, validation

### 🚧 In Progress
- Discord bot deployment (requires token configuration)

### 📋 Backlog
- Custom theme creation
- Additional themes (visual, lore, mechanical)
- Hero data curation from Liquipedia
- Advanced features (winrate recommendations, team validation)

---

## Release Phases & Milestones

---

### 🎯 Phase 1: Foundation (COMPLETED)

**Milestone M1.0: Core MVP** ✅
- **Timeline**: Completed
- **Goals**: Establish domain model and core functionality
- **Deliverables**:
  - [x] CONTEXT.md with full domain model
  - [x] Hero data structure (46+ heroes)
  - [x] Theme data structure (8+ themes)
  - [x] Core logic: theme selection & hero filtering
  - [x] CLI interface
  - [x] Unit test suite (57 core tests)
- **Success Criteria**:
  - Theme suggestions work for all party sizes (1-5)
  - Output format matches specification
  - All tests passing

---

### 🚀 Phase 2: Integration & Enhancement (CURRENT)

**Milestone M2.1: Discord Integration** 🚧
- **Timeline**: Week 1-2
- **Goals**: Deploy bot to Discord for community access
- **Deliverables**:
  - [x] bot.py implementation
  - [x] `!theme [party_size]` command
  - [x] `!tr` alias and `!helptheme` command
  - [ ] Discord bot token configuration
  - [ ] Bot deployed to production server
  - [ ] Basic error handling and logging
- **Success Criteria**:
  - Bot responds to commands in Discord
  - All bot unit tests passing (15 tests)
  - Bot handles invalid inputs gracefully

**Milestone M2.2: Enhanced Theme Selection** ✅
- **Timeline**: Week 2-3
- **Goals**: Improve theme selection intelligence
- **Deliverables**:
  - [x] Filter themes by minimum hero count for party size
  - [x] Weighted random selection (favor themes with more heroes)
  - [x] Position coverage validation
  - [x] filter_themes() function
- **Success Criteria**:
  - Themes with insufficient heroes are filtered out
  - Larger themes have higher selection probability
  - All position-based validations pass

**Milestone M2.3: Position-Based Features** ✅
- **Timeline**: Week 3-4
- **Goals**: Enable lane-based team composition
- **Deliverables**:
  - [x] Lane-based hero grouping (safelane, mid, offlane)
  - [x] Balanced composition suggestions
  - [x] Party composition validation
- **Success Criteria**:
  - Party of 2: safelane(2) OR offlane(2)
  - Party of 3: safelane(2) + mid(1) OR offlane(2) + mid(1)
  - Party of 4: safelane(2) + offlane(2)
  - Party of 5: safelane(2) + mid(1) + offlane(2)

---

### 📈 Phase 3: Data Expansion & Curation

**Milestone M3.1: Hero Data Completion** 🎯
- **Timeline**: Week 5-6
- **Goals**: Complete and verify all hero data
- **Deliverables**:
  - [x] Expand hero database to 108 heroes
  - [ ] Manually curate positions from Liquipedia
  - [ ] Verify all hero IDs match Dota 2 API
  - [ ] Add visual attributes to heroes
- **Success Criteria**:
  - All 108+ Dota 2 heroes represented
  - Position data accuracy >95%
  - Visual attributes for theme matching

**Milestone M3.2: Theme Expansion** 🎯
- **Timeline**: Week 6-7
- **Goals**: Grow theme library to 20+
- **Deliverables**:
  - [ ] Add 12+ new themes
  - [ ] Theme categories (visual, lore, mechanical)
  - [ ] Theme validation scripts
- **Success Criteria**:
  - 20+ themes available
  - Each theme has 5+ matching heroes
  - Themes cover diverse categories

---

### 💡 Phase 4: Advanced Features

**Milestone M4.1: Custom Theme Creation** 🎯
- **Timeline**: Week 8-9
- **Goals**: Allow users to create custom themes
- **Deliverables**:
  - [ ] Discord command: `!addtheme <name> <hero1> <hero2> ...`
  - [ ] Theme persistence (save to themes.json)
  - [ ] Theme validation (minimum heroes, unique names)
  - [ ] List custom themes command
- **Success Criteria**:
  - Users can create themes via Discord
  - Custom themes persist across bot restarts
  - Input validation prevents invalid themes

**Milestone M4.2: Intelligent Recommendations** 🎯
- **Timeline**: Week 9-10
- **Goals**: Provide smarter hero suggestions
- **Deliverables**:
  - [ ] Winrate-based position recommendations
  - [ ] Synergy detection between heroes
  - [ ] Counter-picking suggestions
  - [ ] Team composition validation
- **Success Criteria**:
  - Suggestions consider hero synergy
  - Winrate data integrated (via API or static)
  - Composition warnings for imbalanced teams

**Milestone M4.3: Enhanced User Experience** 🎯
- **Timeline**: Week 10-11
- **Goals**: Improve output and interaction
- **Deliverables**:
  - [ ] Multiple theme suggestions per request
  - [ ] Theme rotation / daily themes
  - [ ] Rich embed formatting for Discord
  - [ ] Hero images in suggestions
- **Success Criteria**:
  - Users can request multiple themes at once
  - Daily theme feature functional
  - Discord messages use rich embeds

---

### 🏆 Phase 5: Production & Scaling

**Milestone M5.1: Production Deployment** 🎯
- **Timeline**: Week 12
- **Goals**: Deploy to production environment
- **Deliverables**:
  - [ ] Docker container for bot
  - [ ] CI/CD pipeline (GitHub Actions)
  - [ ] Automated testing on push
  - [ ] Deployment to cloud hosting
- **Success Criteria**:
  - Bot runs in containerized environment
  - Tests run automatically on PRs
  - Zero-downtime deployments

**Milestone M5.2: Community Features** 🎯
- **Timeline**: Week 13-14
- **Goals**: Build community engagement
- **Deliverables**:
  - [ ] Theme popularity tracking
  - [ ] User statistics (themes used, heroes picked)
  - [ ] Leaderboard for most active users
  - [ ] Feedback collection commands
- **Success Criteria**:
  - Users can view their stats
  - Popular themes are visible
  - Feedback mechanism in place

**Milestone M5.3: Documentation & Onboarding** 🎯
- **Timeline**: Week 14-15
- **Goals**: Improve user onboarding
- **Deliverables**:
  - [ ] Interactive tutorial in Discord
  - [ ] Comprehensive help documentation
  - [ ] Example theme configurations
  - [ ] Video/demo content
- **Success Criteria**:
  - New users can understand features within 2 minutes
  - Help commands cover all features
  - Tutorial completion rate >70%

---

## Priority Matrix

| Priority | Category | Timeline | Status |
|----------|----------|----------|--------|
| P0 (Critical) | Core functionality, bug fixes | Immediate | ✅ Complete |
| P1 (High) | Discord deployment, data accuracy | Week 1-6 | 🚧 In Progress |
| P2 (Medium) | Theme expansion, custom themes | Week 7-9 | ⏳ Planned |
| P3 (Low) | Advanced features, analytics | Week 10+ | ⏳ Backlog |

---

## Dependencies & Blockers

### External Dependencies
- **Discord.py**: Python library for bot functionality (✅ Available)
- **Dota 2 API**: For hero data verification (Optional, can use static data)
- **Liquipedia**: For hero position curation (Manual process)
- **Cloud Hosting**: For production deployment (Future requirement)

### Current Blockers
- ⚠️ **Discord Bot Token**: User action required to configure DISCORD_TOKEN
- ⚠️ **Production Hosting**: No hosting configured yet

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Discord API rate limits | Medium | Medium | Implement caching, rate limiting |
| Data accuracy issues | Low | High | Manual verification, community feedback |
| Bot downtime | Medium | Medium | Monitoring, auto-restart scripts |
| Low user adoption | Medium | High | Community outreach, feature marketing |

---

## Resource Requirements

### Time Estimation
- **Phase 2 (Current)**: 2-4 weeks (Discord deployment + enhancements)
- **Phase 3**: 2-3 weeks (Data curation)
- **Phase 4**: 3-4 weeks (Advanced features)
- **Phase 5**: 2-3 weeks (Production + scaling)

### Tools & Services Needed
- Discord developer account (✅ Available)
- Python 3.8+ environment
- GitHub Actions for CI/CD
- Cloud hosting (AWS, GCP, or similar)

---

## Success Metrics Dashboard

### Phase 2 Goals (Current)
- [x] Core logic tests passing (86+ tests)
- [x] Bot logic tests passing (15 tests)
- [ ] Discord bot deployed and responding
- [ ] 10+ users testing the bot

### Phase 3 Goals
- [ ] 20+ themes available
- [ ] 108+ heroes with verified positions
- [ ] Data accuracy >95%

### Phase 4 Goals
- [ ] Custom theme creation working
- [ ] 50+ unique users/month
- [ ] User satisfaction >4/5 stars

### Phase 5 Goals
- [ ] 99.9% uptime
- [ ] <5 second response time
- [ ] 100+ unique users/month

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2024-XX-XX | Initial roadmap created | Vibe Code |

---

## How to Contribute

1. **Review the roadmap** and identify areas of interest
2. **Check TODOs.md** for detailed task breakdowns
3. **Pick up a task** from the backlog or create a new one
4. **Update this roadmap** when starting/finishing milestones
5. **Test thoroughly** - maintain >72 passing tests

---

## Quick Links

- [README.md](README.md) - Usage and project structure
- [CONTEXT.md](CONTEXT.md) - Domain model and design decisions
- [TODOs.md](TODOs.md) - Detailed task tracking
- [data/heroes.json](data/heroes.json) - Hero data (108 heroes)
- [data/themes.json](data/themes.json) - Theme data (8 themes)

---

*Last Updated: Project Roadmap Creation*
*Next Review: After Milestone M2.1 completion*
