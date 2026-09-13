export interface IngredientSuggestion {
  commonName: string
  scientificName: string
}

export const INGREDIENT_SUGGESTIONS: IngredientSuggestion[] = [
  { commonName: 'Ashwagandha', scientificName: 'Withania somnifera' },
  { commonName: 'Shatavari', scientificName: 'Asparagus racemosus' },
  { commonName: 'Turmeric', scientificName: 'Curcuma longa' },
  { commonName: 'Neem', scientificName: 'Azadirachta indica' },
  { commonName: 'Brahmi', scientificName: 'Bacopa monnieri' },
  { commonName: 'Guggul', scientificName: 'Commiphora wightii' },
  { commonName: 'Tulsi', scientificName: 'Ocimum sanctum' },
  { commonName: 'Amla', scientificName: 'Phyllanthus emblica' },
  { commonName: 'Triphala', scientificName: '(blend: Amalaki, Bibhitaki, Haritaki)' },
  { commonName: 'Guduchi', scientificName: 'Tinospora cordifolia' },
  { commonName: 'Arjuna', scientificName: 'Terminalia arjuna' },
  { commonName: 'Licorice', scientificName: 'Glycyrrhiza glabra' },
  { commonName: 'Ginger', scientificName: 'Zingiber officinale' },
  { commonName: 'Fenugreek', scientificName: 'Trigonella foenum-graecum' },
  { commonName: 'Aloe Vera', scientificName: 'Aloe barbadensis' },
]

export const UNIT_OPTIONS = ['mg', 'g', 'mcg', 'ml', '%', 'IU', 'drops', 'tsp'] as const
