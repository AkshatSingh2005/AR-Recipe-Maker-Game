from .nutrition import calculate_health_score, safe_float

class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, product):
        self.items.append(product)

    def total_calories(self):
        return sum(safe_float(item.get('calories', 0)) for item in self.items)

    def total_fat(self):
        return sum(safe_float(item.get('fat', 0)) for item in self.items)

    def total_protein(self):
        return sum(safe_float(item.get('protein', 0)) for item in self.items)

    def total_health_score(self):
        return sum(calculate_health_score(item['ingredient_analysis']) for item in self.items)

    def challenge_1500_kcal(self):
        return self.total_calories() <= 1500

    def challenge_protein_rich(self):
        return self.total_protein() >= 60 and self.total_fat() <= 50

    def game_score(self):
        score = self.total_health_score()
        if self.challenge_1500_kcal():
            score += 50
        if self.challenge_protein_rich():
            score += 30
        return score

    def clear(self):
        self.items = []

