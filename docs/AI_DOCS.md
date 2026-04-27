# AI-Assisted Development: Lessons Learned

My Farm Advisor dashboard was developed using opencode—an interactive CLI tool for software engineering tasks. This document captures key technical hurdles and how AI-assisted development helped overcome them.

## Technical Hurdles Overcome

### 1. JavaScript Syntax Errors in Embedded HTML

**Problem**: Large HTML file (>700 lines) with embedded JavaScript. Multiple syntax errors caused "Illegal return statement" and "Unexpected token" errors.

**Root Cause**: 
- Duplicate sections of code that were accidentally pasted
- Brace mismatch after multiple editing passes
- Missing closing braces in function declarations

**How AI Helped**:
- Iterative node --check validation after each edit
- Python-based brace counting to isolate problem areas
- Breaking large edits into smaller, testable units

**Key Takeaway**: Use automated syntax checking at every step when working with embedded scripts in HTML.

### 2. Chart.js Configuration Complexity

**Problem**: Attempted to add vertical mean line annotation to OM distribution using chartjs-plugin-annotation. Configuration was error-prone and caused nested brace issues.

**Solution**: Simplified to display mean in title text rather than a true chart annotation.

**Alternative Approach Considered**: 
- Custom canvas drawing (used later for correlation heatmap)
- Direct title/subtitle display for simple annotations

**Key Takeaway**: When a library feature causes complexity, consider simpler alternatives or custom Canvas implementations.

### 3. Null Reference Errors After UI Changes

**Problem**: Removed temperature/precipitation chart sections from HTML but corresponding JavaScript still tried to update those charts, causing "Cannot read properties of undefined" errors.

**Root Cause**: Code cleanup was incomplete—removed HTML but not all references.

**Solution**: Added null guards before accessing chart elements:
```javascript
if (!tempChart || !precipChart) return;
```

**Key Takeaway**: When removing UI components, trace all code paths that reference them.

### 4. Leaflet Map Initialization Errors

**Problem**: "latLngToLayerPoint" error when adding layers to maps before they were fully initialized.

**Solution**: Added null checks after map initialization:
```javascript
if (!omMap) { console.error('OM map failed to initialize'); return; }
```

**Key Takeaway**: Always validate map/container existence before adding layers.

### 5. Iterative Requirement Changes

**Problem**: Dashboard layout changed multiple times (2x2 grid, which maps, OM distribution vs correlation, etc.)

**Solution**: Implemented modular structure with clear section IDs, making changes surgical rather than wholesale rewrites.

**Key Takeaway**: Build modular, well-structured code from the start—requirements will evolve.

### 6. Reappearing Errors

**Problem**: Some errors appeared to be fixed but later returned. For example:

- **CRS/coordinates checked** with logging added, verified working, but later edits to map initialization code reintroduced issues because the fix was not applied comprehensively
- **Removed layer controls** in one map section but another section still referenced the same layer variables, causing type errors
- **Null checks added** to one function, but a similar pattern elsewhere was not updated consistently

**Pattern**: Errors often returned when:
- Similar code existed in multiple places and only one was fixed
- Changes were made to one section without checking related sections
- Fixes were applied to the immediate problem without checking for systemic patterns

**Solution**: 
- Searched the entire file with grep for similar patterns before finalizing fixes
- Added comprehensive null checks at function entry points rather than scattered throughout
- Verified changes did not break other map sections or chart initializations

**Key Takeaway**: In AI-assisted editing, scan for similar patterns across the entire codebase—fixes to one instance should be applied everywhere the same pattern appears.

## Approaches That Worked Well

### 1. Continuous Validation
- Run node --check after every JavaScript edit
- Check brace balance before moving on

### 2. Read-Based Editing
- Always read the surrounding context before making edits
- Understand existing code patterns

### 3. Modular Functions
- Keep functions focused and single-purpose
- Easier to debug when issues arise

### 4. Null Guards
- Defensive programming for optional UI components
- Prevents cascading errors

### 5. Pattern Scanning
- After fixing an error, grep for similar patterns that might have the same issue
- Apply fixes comprehensively, not just to the immediate instance

### 6. Stage Changes at Good Points

**Problem**: Without regular staging, work can get lost or overwritten. Multiple edit passes without committing "good states" made it harder to track deviations and recover if edits went wrong.

**Solution**: 
- Stage files when they reach a working state
- Commit regularly so there's a track record of deviations
- Use git diff --staged to review what will be committed

**Key Takeaway**: Version control is your safety net—use it to capture good states, not just final states.

## Approaches to Avoid

### 1. Large Editing Passes
- Big edits are harder to debug when they fail
- Break into smaller, testable chunks

### 2. Complex Library Configurations
- When a library feature is complex, consider alternatives
- Custom Canvas often simpler than fighting a library

### 3. Assumption-Based Changes
- Do not assume what variables exist—verify with grep
- Do not assume code structure—read it first

### 4. Single-Point Fixes
- Do not just fix the displayed error—check for systemic issues
- If one function has a null check, similar functions probably need one too

## Summary

Key lessons from AI-assisted development:

1. **Validate frequently** — catch errors early
2. **Read before editing** — understand context first  
3. **Keep it modular** — makes changes surgical
4. **Add null guards** — defensive programming
5. **Simpler is better** — avoid over-engineering
6. **Scan for patterns** — fix comprehensively, not just locally
7. **Recheck after edits** — errors can reappear if related code was not updated

This document captures the development journey and lessons learned for future AI-assisted projects.
EOF
echo "File created successfully"
