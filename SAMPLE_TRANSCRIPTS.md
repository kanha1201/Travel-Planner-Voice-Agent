# Sample Test Transcripts

This document contains sample user interactions for testing the Voice Travel Planner system.

## Usage

These transcripts can be used for:
- **Manual Testing**: Speak these phrases into the voice interface
- **Quality Evaluation**: Compare system responses to expected behavior
- **Regression Testing**: Ensure system works after changes
- **Documentation**: Show example interactions

---

## Category 1: Basic Trip Planning

### Test 1.1: Simple 2-Day Trip Request

**User**: "Plan a two day trip to Jaipur"

**Expected Behavior**:
- System calls `search_pois` with default interests
- System calls `build_itinerary` with POIs
- Response includes Day 1 and Day 2 with Morning, Afternoon, Evening activities
- Sources include OpenStreetMap POI URLs

**Success Criteria**:
- ✅ Itinerary has 2 days
- ✅ Each day has multiple activities
- ✅ Activities are time-stamped
- ✅ Sources are available (click "i" button)

---

### Test 1.2: Trip with Specific Interests

**User**: "Plan a 3-day cultural and historical trip to Jaipur"

**Expected Behavior**:
- System calls `search_pois` with interests: ["culture", "history"]
- System calls `build_itinerary` with duration_days=3
- Response focuses on cultural and historical sites

**Success Criteria**:
- ✅ Itinerary has 3 days
- ✅ POIs are cultural/historical (museums, monuments, palaces)
- ✅ Activities are relevant to interests

---

### Test 1.3: Trip with Pace Preference

**User**: "Plan a relaxed 2-day trip to Jaipur"

**Expected Behavior**:
- System calls `search_pois` with pace="relaxed"
- System calls `build_itinerary` with pace="relaxed"
- Response has 2-3 activities per day (relaxed pace)

**Success Criteria**:
- ✅ Fewer activities per day (relaxed pace)
- ✅ More time between activities
- ✅ Less rushed schedule

---

### Test 1.4: Trip with Budget Constraint

**User**: "Plan a budget-friendly 2-day trip to Jaipur"

**Expected Behavior**:
- System calls `search_pois` with constraints={"budget": "budget"}
- Response includes budget-friendly options

**Success Criteria**:
- ✅ POIs are budget-friendly (free attractions, affordable restaurants)
- ✅ No luxury options included

---

## Category 2: Itinerary Modifications

### Test 2.1: Remove Activity

**User**: "Remove Day 1 morning activity"

**Expected Behavior**:
- System extracts current itinerary from context
- System calls `build_itinerary` with modified POI list (removed morning POI)
- Response shows updated itinerary without Day 1 morning activity

**Success Criteria**:
- ✅ Day 1 morning activity is removed
- ✅ Other activities remain
- ✅ Itinerary is restructured correctly
- ✅ UI updates to show new itinerary

---

### Test 2.2: Add Activity

**User**: "Add a restaurant to Day 2 evening"

**Expected Behavior**:
- System calls `search_pois` for restaurants
- System calls `build_itinerary` with new restaurant added
- Response shows updated Day 2 with evening restaurant

**Success Criteria**:
- ✅ Day 2 evening has restaurant activity
- ✅ Restaurant is appropriate for evening
- ✅ Time slots are valid

---

### Test 2.3: Change Activity

**User**: "Change Day 1 afternoon activity to a museum"

**Expected Behavior**:
- System calls `search_pois` for museums
- System calls `build_itinerary` with museum replacing afternoon activity
- Response shows updated Day 1 with museum in afternoon

**Success Criteria**:
- ✅ Day 1 afternoon has museum
- ✅ Old activity is replaced
- ✅ Time slots are valid

---

### Test 2.4: Extend Trip Duration

**User**: "Extend the trip to 3 days"

**Expected Behavior**:
- System calls `search_pois` for additional POIs
- System calls `build_itinerary` with duration_days=3
- Response shows 3-day itinerary

**Success Criteria**:
- ✅ Itinerary has 3 days
- ✅ New activities are added
- ✅ Existing activities are preserved

---

## Category 3: Question Answering

### Test 3.1: Why Question

**User**: "Why is Hawa Mahal a recommended tourist destination?"

**Expected Behavior**:
- System calls `retrieve_city_guidance` with query about Hawa Mahal
- Response includes factual information with citations
- Sources include Wikivoyage/Wikipedia URLs

**Success Criteria**:
- ✅ Response explains why Hawa Mahal is recommended
- ✅ Sources are cited (check "i" button)
- ✅ Information is factual (not made up)

---

### Test 3.2: What Question

**User**: "What are the best cultural sites in Jaipur?"

**Expected Behavior**:
- System calls `retrieve_city_guidance` with query about cultural sites
- Response lists cultural attractions with explanations
- Sources are provided

**Success Criteria**:
- ✅ Response lists cultural sites
- ✅ Each site has brief explanation
- ✅ Sources are cited

---

### Test 3.3: Safety Question

**User**: "Is Jaipur safe for tourists?"

**Expected Behavior**:
- System calls `retrieve_city_guidance` with query about safety
- Response includes safety information from travel guides
- Sources are provided

**Success Criteria**:
- ✅ Response addresses safety concerns
- ✅ Information is from reliable sources
- ✅ Sources are cited

---

### Test 3.4: Cultural Question

**User**: "What should I know about local customs in Jaipur?"

**Expected Behavior**:
- System calls `retrieve_city_guidance` with query about customs
- Response includes cultural etiquette information
- Sources are provided

**Success Criteria**:
- ✅ Response covers local customs
- ✅ Practical advice is given
- ✅ Sources are cited

---

## Category 4: Clarifying Questions

### Test 4.1: Missing Duration

**User**: "Plan a trip to Jaipur"

**Expected Behavior**:
- System calls `ask_clarifying_question` about trip duration
- Response asks: "How many days would you like to spend in Jaipur?"

**Success Criteria**:
- ✅ System asks for missing information
- ✅ Question is clear and helpful
- ✅ Only 1-2 questions asked (not overwhelming)

---

### Test 4.2: Missing Interests

**User**: "Plan a 2-day trip"

**Expected Behavior**:
- System may ask about interests or use default interests
- If asking: "What are your main interests? (e.g., culture, food, history)"

**Success Criteria**:
- ✅ System handles missing information gracefully
- ✅ Either asks clarifying question or uses sensible defaults

---

## Category 5: Complex Requests

### Test 5.1: Multi-Constraint Request

**User**: "Plan a 3-day budget-friendly trip focused on architecture and food, with a relaxed pace"

**Expected Behavior**:
- System calls `search_pois` with:
  - interests: ["architecture", "food"]
  - constraints: {"budget": "budget", "pace": "relaxed"}
- System calls `build_itinerary` with duration_days=3, pace="relaxed"
- Response satisfies all constraints

**Success Criteria**:
- ✅ All constraints are met
- ✅ POIs match interests (architecture, food)
- ✅ Budget-friendly options
- ✅ Relaxed pace (2-3 activities/day)

---

### Test 5.2: Indoor-Only Request

**User**: "Plan a 2-day indoor-only trip to Jaipur"

**Expected Behavior**:
- System calls `search_pois` with constraints={"indoor_only": true}
- Response includes only indoor attractions (museums, palaces, restaurants)

**Success Criteria**:
- ✅ All activities are indoor
- ✅ No outdoor-only attractions

---

### Test 5.3: Accessibility Request

**User**: "Plan an accessible 2-day trip to Jaipur"

**Expected Behavior**:
- System calls `search_pois` with constraints={"accessibility": true}
- Response includes accessible attractions

**Success Criteria**:
- ✅ Accessibility is considered
- ✅ Accessible options are prioritized

---

## Category 6: Edge Cases

### Test 6.1: Very Short Trip

**User**: "Plan a half-day trip to Jaipur"

**Expected Behavior**:
- System may ask for clarification or plan a single-day trip
- Response includes activities for part of a day

**Success Criteria**:
- ✅ System handles unusual duration gracefully
- ✅ Response is still useful

---

### Test 6.2: Very Long Trip

**User**: "Plan a 7-day trip to Jaipur"

**Expected Behavior**:
- System calls `search_pois` with max_results=30+ to get enough POIs
- System calls `build_itinerary` with duration_days=7
- Response includes 7 days of activities

**Success Criteria**:
- ✅ Itinerary has 7 days
- ✅ Each day has activities
- ✅ Variety across days

---

### Test 6.3: Ambiguous Request

**User**: "I want to see things"

**Expected Behavior**:
- System may ask clarifying questions or use default interests
- Response includes popular attractions

**Success Criteria**:
- ✅ System handles ambiguity
- ✅ Response is still helpful

---

## Category 7: Follow-up Questions

### Test 7.1: Question About Itinerary

**User**: "Why did you choose these activities?"

**Expected Behavior**:
- System explains reasoning based on:
  - User preferences (if provided)
  - POI characteristics
  - Travel time considerations
  - Pace preferences

**Success Criteria**:
- ✅ Explanation is clear
- ✅ Reasoning is logical
- ✅ User preferences are referenced

---

### Test 7.2: Question About Specific POI

**User**: "Tell me more about City Palace"

**Expected Behavior**:
- System calls `retrieve_city_guidance` with query about City Palace
- Response includes detailed information with citations

**Success Criteria**:
- ✅ Detailed information provided
- ✅ Sources are cited
- ✅ Information is relevant

---

## Evaluation Checklist

For each test transcript, verify:

- [ ] **Response Time**: < 20 seconds total
- [ ] **Accuracy**: Information is correct
- [ ] **Relevance**: Response matches user intent
- [ ] **Completeness**: All requested information provided
- [ ] **Sources**: Sources are cited (for factual questions)
- [ ] **Formatting**: Response is well-formatted
- [ ] **Tool Usage**: Appropriate tools are called
- [ ] **Error Handling**: Errors are handled gracefully

---

## Notes

- **Voice Input**: These transcripts should be spoken naturally, not read verbatim
- **Variations**: Users may phrase requests differently - system should handle variations
- **Context**: Some tests assume previous conversation context (e.g., modification tests)
- **Sources**: Always check sources via "i" button for factual questions

---

## See Also

- [EVALS.md](EVALS.md) - How to run evaluations
- [TOOLS.md](TOOLS.md) - Tool documentation
- [README.md](README.md) - System setup

