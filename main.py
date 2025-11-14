
import os
import sys
from src import CustomerServiceAgent

def main():
    try:
        agent = CustomerServiceAgent()
        print("Customer Service Agent Started!")
        print("Type 'quit' to exit\n")
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        print("Please check that all data files are properly formatted.")
        return
    
    customer_id = "cust_123"  # In real app, this would come from auth system
    
    while True:
        try:
            message = input("Customer: ").strip()
            
            if message.lower() == 'quit':
                break
                
            if not message:
                continue
            
            # Process the message
            result = agent.process_message(customer_id, message)
            
            # Display response
            print(f"\nAgent: {result['response']}")
            print(f"\n[Persona: {result['detected_persona']['type']} "
                  f"(confidence: {result['detected_persona']['confidence']})]")
            
            if result['escalation']:
                print(f"[ESCALATION: {result['escalation']['level']} - {result['escalation']['reason']}]")
                print(f"[Contact: {result['escalation']['contact']}]")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error processing message: {e}")
            continue

if __name__ == "__main__":
    main()