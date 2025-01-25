spam_words = ["бесплатно", "скидка", "скидку"]

def check_for_spam(message) -> bool:
	if message in spam_words:
		return True
	else:
		return False