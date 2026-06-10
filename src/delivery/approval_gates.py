import sys

def print_banner(title: str, color_code: str = "94"):
    """Prints a styled banner for terminal headers."""
    border = "=" * 70
    print(f"\033[1;\033[{color_code}m{border}")
    print(f"{title.center(70)}")
    print(f"{border}\033[0m")

def print_section(title: str, color_code: str = "94"):
    """Prints a styled section header."""
    print(f"\n\033[1;\033[{color_code}m--- {title} ---\033[0m")

def get_input(prompt: str, valid_choices: list[str]) -> str:
    """Helper to get user input with validation."""
    choices_str = "/".join(valid_choices)
    while True:
        try:
            val = input(f"{prompt} ({choices_str}): ").strip().upper()
            if val in [c.upper() for c in valid_choices]:
                return val
            print(f"\033[91mInvalid choice. Please choose one of {valid_choices}.\033[0m")
        except (KeyboardInterrupt, EOFError):
            print("\n\033[91mProcess interrupted. Defaulting to Reject.\033[0m")
            return "R"

def approval_gate(gate_number: int, label: str, payload: dict) -> bool:
    """
    Displays the payload to the user in a formatted terminal preview.
    Prompts: [A]pprove / [R]eject / [F]eedback (for Gates 1 & 2) or [A]pprove / [R]eject (for Gates 3 & 4)
    
    Returns:
        bool: True if approved, False if rejected/feedback requested.
    """
    import os
    req_approval = os.getenv("REQUIRE_TERMINAL_APPROVAL", "true").lower()
    if req_approval in ("false", "0", "no"):
        print(f"\033[93m[Bypass] REQUIRE_TERMINAL_APPROVAL is set to '{req_approval}'. Automatically approving Gate {gate_number}.\033[0m")
        return True

    if gate_number == 1:
        # Gate 1: Weekly Pulse Review
        print_banner(f"APPROVAL GATE 1: WEEKLY PULSE REVIEW - {label.upper()}", "94")
        
        # Display themes and quotes
        print_section("THEMES & REPRESENTATIVE QUOTES", "96")
        themes = payload.get("themes", [])
        quotes = payload.get("quotes", [])
        for idx, t in enumerate(themes):
            print(f"\033[1mTheme {idx+1}: {t}\033[0m")
            if idx < len(quotes):
                print(f"  Quote: \"{quotes[idx]}\"")
        
        # Display summary
        print_section("WEEKLY SUMMARY", "96")
        weekly_summary = payload.get("weekly_summary", "")
        print(weekly_summary)
        
        # Display sentiment
        print_section("CUSTOMER SENTIMENT", "96")
        sentiment = payload.get("sentiment", {})
        pos = sentiment.get("positive", 0)
        neg = sentiment.get("negative", 0)
        neu = sentiment.get("neutral", 0)
        print(f"Positive: \033[92m{pos}%\033[0m | Negative: \033[91m{neg}%\033[0m | Neutral: \033[93m{neu}%\033[0m")
        
        # Display action ideas
        print_section("ACTION RECOMMENDATIONS", "96")
        action_ideas = payload.get("action_ideas", [])
        for idx, idea in enumerate(action_ideas, start=1):
            print(f"  {idx}. {idea}")
            
        print("\n" + "="*70)
        choice = get_input("\033[1mDo you approve the Weekly Pulse summary and action ideas?\033[0m", ["A", "R", "F"])
        
        if choice == "A":
            print("\033[92mGate 1 APPROVED.\033[0m")
            return True
        elif choice == "F":
            feedback = input("\033[93mEnter your feedback for re-generation:\033[0m ").strip()
            payload["feedback"] = feedback
            print("\033[91mGate 1 REJECTED with feedback. Re-generating...\033[0m")
            return False
        else:
            print("\033[91mGate 1 REJECTED. Re-generating...\033[0m")
            return False

    elif gate_number == 2:
        # Gate 2: Fee Explainer Review
        print_banner(f"APPROVAL GATE 2: FEE EXPLAINER REVIEW - {label.upper()}", "94")
        
        # Display scenario
        print_section(f"SCENARIO: {payload.get('scenario', 'Mutual Fund Exit Load')}", "96")
        
        # Display bullets
        print_section("EXPLANATION BULLETS", "96")
        bullets = payload.get("bullets", [])
        for idx, bullet in enumerate(bullets, start=1):
            print(f"  - {bullet}")
            
        # Display sources
        print_section("SOURCES", "96")
        sources = payload.get("sources", [])
        for src in sources:
            print(f"  - {src}")
            
        # Display date
        print_section("LAST CHECKED", "96")
        print(payload.get("last_checked", "N/A"))
        
        print("\n" + "="*70)
        choice = get_input("\033[1mDo you approve the Fee Explainer bullets and sources?\033[0m", ["A", "R", "F"])
        
        if choice == "A":
            print("\033[92mGate 2 APPROVED.\033[0m")
            return True
        elif choice == "F":
            feedback = input("\033[93mEnter your feedback for re-generation:\033[0m ").strip()
            payload["feedback"] = feedback
            print("\033[91mGate 2 REJECTED with feedback. Re-generating...\033[0m")
            return False
        else:
            print("\033[91mGate 2 REJECTED. Re-generating...\033[0m")
            return False

    elif gate_number == 3:
        # Gate 3: Google Doc Write
        print_banner(f"APPROVAL GATE 3: GOOGLE DOC APPEND - {label.upper()}", "95")
        
        print(f"\033[1mTarget Document ID:\033[0m {payload.get('document_id')}")
        print(f"\033[1mTarget Week:\033[0m {payload.get('iso_week')}")
        print(f"\033[1mWrite Mode:\033[0m {'UPDATE (Idempotent)' if payload.get('is_update') else 'INSERT (New Entry)'}")
        
        print_section("PREVIEW OF FORMATTED ENTRY", "95")
        # Format preview
        pulse_summary = payload.get("weekly_pulse", {}).get("weekly_summary", "")
        print(f"\033[3m{pulse_summary[:300]}...\033[0m")
        print(f"And {len(payload.get('explanation_bullets', []))} exit load bullets...")
        
        print("\n" + "="*70)
        choice = get_input("\033[1mConfirm write to Google Doc?\033[0m", ["A", "R"])
        
        if choice == "A":
            print("\033[92mGate 3 APPROVED. Executing Google Doc write...\033[0m")
            return True
        else:
            print("\033[91mGate 3 REJECTED. Aborting Google Doc write...\033[0m")
            return False

    elif gate_number == 4:
        # Gate 4: Gmail Draft Write
        print_banner(f"APPROVAL GATE 4: GMAIL DRAFT CREATION - {label.upper()}", "95")
        
        print(f"\033[1mRecipient:\033[0m {payload.get('recipient')}")
        print(f"\033[1mSubject:\033[0m {payload.get('subject')}")
        
        print_section("EMAIL BODY PREVIEW", "95")
        print(payload.get("body"))
        
        print("\n" + "="*70)
        choice = get_input("\033[1mConfirm creation of Gmail draft?\033[0m", ["A", "R"])
        
        if choice == "A":
            print("\033[92mGate 4 APPROVED. Creating Gmail draft...\033[0m")
            return True
        else:
            print("\033[91mGate 4 REJECTED. Aborting Gmail draft creation...\033[0m")
            return False

    return False
