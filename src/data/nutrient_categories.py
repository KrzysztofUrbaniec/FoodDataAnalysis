'''
This module contatins a dictionary of nutrients, that can be used for quick selection of specific types during downloading data from FDC database
'''

nutrients = {
    'proximates': ['Energy','Water','Protein','Total lipid (fat)','Carbohydrate, by difference','Ash'],
    'vitamins': ['Vitamin K (Dihydrophylloquinone)','Vitamin K (phylloquinone)','Folate, total',
           'Vitamin C, total ascorbic acid','Niacin','Vitamin B-6','Riboflavin','Thiamin','Pantothenic acid',
           'Vitamin A, RAE','Lutein + zeaxanthin','Vitamin D (D2 + D3)']
    'minerals': ['Calcium, Ca','Potassium, K','Zinc, Zn','Selenium, Se','Manganese, Mn','Phosphorus, P',
           'Magnesium, Mg','Copper, Cu','Iron, Fe','Sodium, Na']
    'essential_aminoacids': ['Histidine','Isoleucine','Leucine','Lysine','Methionine','Phenylalanine','Threonine','Tyrosine','Valine']
    'organic_acids': ['Citric acid','Malic acid','Oxalic acid','Quinic acid']
}