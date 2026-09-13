import type {
  Session,
  Classification,
  AskResponse,
  Objective,
  Category,
} from '../types'

export function createSession(): Session {
  return {
    session_id: crypto.randomUUID(),
    jurisdiction: null,
    product: {
      name: '',
      composition: [],
      intended_use: null,
      classical_basis: null,
      classical_reference: '',
      novelty: null,
      ingredient_sources: [],
      geographic_origin: '',
      biological_origin_known: null,
      biological_origin_region: '',
      development_status: null,
    },
    protection_target: null,
    objective: [],
    classification: null,
  }
}

const classifications: Record<Category, Classification> = {
  classical_generic: {
    category: 'classical_generic',
    reasons: [
      'Your formulation is based on a classical Ayurvedic text reference, which places it in the Classical/Generic category under the Drugs and Cosmetics Act, 1940.',
      'Classical formulations are not eligible for product patents as they are part of prior traditional knowledge.',
      'Regulatory pathway: licensing under ASU Drug Manufacturing License (Rule 157-B, D&C Rules).',
    ],
    confidence: 'high',
  },
  proprietary: {
    category: 'proprietary',
    reasons: [
      'Your formulation appears to be a new combination or modification of known ingredients, qualifying as a Proprietary Ayurvedic Medicine.',
      'Proprietary products may be eligible for patent protection if they demonstrate novelty and inventive step.',
      'Regulatory pathway: Proprietary ASU license under D&C Act, 1940; consider patent filing under Patents Act, 1970.',
    ],
    confidence: 'high',
  },
  new_drug: {
    category: 'new_drug',
    reasons: [
      'Your product involves a new molecule or novel therapeutic claim, which classifies it as a New Drug under the New Drugs and Clinical Trials Rules, 2019.',
      'New Drugs require CDSCO approval and clinical trial data before marketing.',
      'Patent protection may be available under Patents Act, 1970, §2(1)(j).',
    ],
    confidence: 'medium',
  },
  phytopharmaceutical: {
    category: 'phytopharmaceutical',
    reasons: [
      'Your formulation is a purified and standardized plant extract with defined markers, fitting the Phytopharmaceutical Drug category under D&C Rules, 2016.',
      'Phytopharmaceuticals require quality standardization and may qualify for patent protection under §3(p) evaluation.',
      'Regulatory pathway: CDSCO approval with evidence of standardization and safety.',
    ],
    confidence: 'medium',
  },
  nutraceutical_ayurveda_aahar: {
    category: 'nutraceutical_ayurveda_aahar',
    reasons: [
      'Your product is intended as a food supplement, classifying it under FSSAI as Ayurveda-Aahar (Health Supplement) per FSS Regulations, 2022.',
      'Ayurveda-Aahar products cannot claim therapeutic efficacy and are regulated by FSSAI, not CDSCO.',
      'No patent protection for the food form, but process patents may be available.',
    ],
    confidence: 'high',
  },
  cosmetic: {
    category: 'cosmetic',
    reasons: [
      'Your product is intended for cosmetic use, placing it under the Drugs and Cosmetics Act cosmetic regulations.',
      'Cosmetics require a Cosmetic Manufacturing License and are regulated by CDSCO.',
      'No therapeutic claims permitted; trademark protection is the primary IP route.',
    ],
    confidence: 'high',
  },
  unresolved: {
    category: 'unresolved',
    reasons: [
      'The information provided does not map cleanly to a single regulatory category.',
      'Some answers are missing or ambiguous, which prevents a confident classification.',
      'Consider revising your questionnaire answers or consulting a specialist for case-specific guidance.',
    ],
    confidence: 'low',
  },
}

export function classifyProduct(session: Session): Classification {
  const p = session.product
  let category: Category = 'proprietary'

  if (session.protection_target === 'brand') {
    category = 'proprietary'
  } else if (p.intended_use === 'cosmetic') {
    category = 'cosmetic'
  } else if (p.intended_use === 'food_supplement') {
    category = 'nutraceutical_ayurveda_aahar'
  } else if (p.classical_basis === 'yes') {
    category = 'classical_generic'
  } else if (p.novelty === 'new_combination' || p.novelty === 'modified') {
    if (p.ingredient_sources.includes('plant') && p.ingredient_sources.length === 1) {
      category = 'phytopharmaceutical'
    } else {
      category = 'proprietary'
    }
  } else if (p.novelty === 'existing') {
    category = 'classical_generic'
  } else if (p.development_status === 'filed_ip' || p.development_status === 'marketed') {
    category = 'new_drug'
  } else if (session.protection_target === 'unsure') {
    category = p.intended_use === 'therapeutic' ? 'proprietary' : 'nutraceutical_ayurveda_aahar'
  } else if (session.protection_target === 'traditional_knowledge' || session.protection_target === 'process') {
    category = 'proprietary'
  } else {
    category = 'unresolved'
  }

  return classifications[category]
}

export function askQuestion(_question: string, _objectives: Objective[]): Promise<AskResponse> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        answer:
          'Under the Patents Act, 1970, §3(p), traditional knowledge-based formulations are not patentable unless they demonstrate a significant enhancement in known efficacy through a new form or combination. Your product, if based on a classical Ayurvedic formulation, would likely fall under this exclusion. However, if the formulation involves a novel combination or modification with improved therapeutic effect, a product patent may be pursued. Regulatory approval would still be required under the Drugs and Cosmetics Act, 1940, as an ASU (Ayurveda, Siddha, Unani) drug.',
        citations: [
          {
            doc_id: 'Patents Act, 1970',
            section: '§3(p)',
            excerpt:
              'An invention which in effect, is traditional knowledge or which is an aggregation or duplication of the properties of traditionally known component or components.',
          },
          {
            doc_id: 'Drugs and Cosmetics Act, 1940',
            section: '§3(a), Rule 157-B',
            excerpt:
              'ASU drugs include medicines based on Ayurveda, Siddha, and Unani systems. Manufacturing license required under Rule 157-B of the D&C Rules.',
          },
          {
            doc_id: 'Biodiversity Act, 2002',
            section: '§3, §6',
            excerpt:
              'Access to biological resources and associated traditional knowledge requires approval from the National Biodiversity Authority. Results of research on biological resources cannot be commercialized without NBA approval.',
          },
        ],
        confidence: 'high',
        abstained: false,
      })
    }, 800)
  })
}

export function getAbstentionResponse(): AskResponse {
  return {
    answer:
      'Insufficient authoritative evidence in our corpus to answer this reliably. This may be outside the scope of our current legal database, or the question may require case-specific analysis. We recommend consulting a registered IP facilitator or patent agent for this query.',
    citations: [],
    confidence: 'abstain',
    abstained: true,
  }
}
