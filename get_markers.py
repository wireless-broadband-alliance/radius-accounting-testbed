import logging


def select_markers():
    """Select markers from a list."""

    # TODO: These should be generated dynamically
    options_mapping = {
        "1": "core",
        "2": "core_download",
        "3": "core_upload",
        "4": "openroaming",
    }
    print("\nSelect marker(s) from the list:")
    for key, value in options_mapping.items():
        print(f"{key}) {value}")
    print("")

    selected_options = []
    user_input = input("Enter your options (comma-separated numbers): ")
    selected_options = [
        options_mapping.get(choice.strip(), "") for choice in user_input.split(",")
    ]
    selected_options = [option for option in selected_options if option]

    return ",".join(selected_options)


def prompt_yes_no(prompt_message):
    user_input = input(f"{prompt_message} (yes/no): ").strip().lower()

    if user_input == "yes":
        return True
    elif user_input == "no":
        return False
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")
        return prompt_yes_no(prompt_message)


# Example usage:
if __name__ == "__main__":
    prompt_message = "Do you want to continue?"
    print(prompt_yes_no(prompt_message))
