# Complete Workflow Specification - Gem-Flux MCP Server

**Type**: Workflow Specification
**Status**: Phase 0 - Cleanroom Specification
**Version**: MVP v0.1.0

## Prerequisites

- Read: 001-system-overview.md (for system architecture understanding)
- Read: 003-build-media-tool.md (for media creation)
- Read: 004-build-model-tool.md (for model building)
- Read: 005-gapfill-model-tool.md (for gapfilling process)
- Read: 006-run-fba-tool.md (for flux balance analysis)
- Read: 008-compound-lookup-tools.md (for compound lookups)
- Read: 009-reaction-lookup-tools.md (for reaction lookups)

## Purpose

This specification describes the complete end-to-end workflow for building, analyzing, and interpreting metabolic models using the Gem-Flux MCP server. It demonstrates how the four core tools (build_media, build_model, gapfill_model, run_fba) and database lookup tools work together to enable AI-assisted metabolic modeling workflows. This workflow represents the primary use case for the MVP and serves as a reference for implementation and testing.

## Workflow Overview

**Complete Metabolic Modeling Workflow**:
```
1. Create Growth Medium (build_media)
   ↓
2. Build Draft Model (build_model)
   ↓
3. Gapfill for Growth (gapfill_model)
   ↓
4. Run FBA Analysis (run_fba)
   ↓
5. Interpret Results (database lookup tools)
```

**Data Flow**:
```
Compound IDs → Media (media_id)
                ↓
Protein Sequences → Draft Model (model_id)
                     ↓
model_id + media_id → Gapfilled Model (model_id.gf)
                       ↓
model_id.gf + media_id → Fluxes + Growth Rate
                          ↓
Reaction/Compound IDs → Human-Readable Explanations
```

## Complete Example: E. coli Model Building and Analysis

### Scenario

**User Goal**: Build a metabolic model for E. coli strain K-12, analyze growth in glucose minimal medium, and understand which pathways are active during aerobic respiration.

**User Has**:
- 150 protein sequences from E. coli K-12 genome
- Knowledge that E. coli is Gram-negative
- Interest in aerobic glucose metabolism

**Expected Outcome**:
- Functional metabolic model
- Growth rate prediction
- Active pathway identification
- Human-readable metabolic interpretation

### Step 1: Create Glucose Minimal Medium

**User Request**: "Create a glucose minimal medium for E. coli growth under aerobic conditions"

**AI Assistant Reasoning**:
1. E. coli minimal medium requires:
   - Carbon source: D-Glucose (cpd00027)
   - Electron acceptor: O2 (cpd00007)
   - Essential nutrients: H2O, NH3, phosphate, sulfate, trace metals
2. Aerobic conditions: Allow oxygen uptake
3. Limit glucose uptake to realistic rate (5 mmol/gDW/h)

**AI Assistant Action** - Call build_media:
```json
{
  "compounds": [
    "cpd00027",  "cpd00007",  "cpd00001",  "cpd00009",
    "cpd00011",  "cpd00013",  "cpd00067",  "cpd00099",
    "cpd00149",  "cpd00205",  "cpd00254",  "cpd00971",
    "cpd10515",  "cpd10516",  "cpd00063",  "cpd00030",
    "cpd00034",  "cpd00048",  "cpd00058",  "cpd00244"
  ],
  "default_uptake": 100.0,
  "custom_bounds": {
    "cpd00027": [-5, 100],
    "cpd00007": [-10, 100]
  }
}
```

**Response**:
```json
{
  "success": true,
  "media_id": "media_20251027_a3f9b2",
  "compounds": [
    {
      "id": "cpd00027",
      "name": "D-Glucose",
      "formula": "C6H12O6",
      "bounds": [-5, 100]
    },
    {
      "id": "cpd00007",
      "name": "O2",
      "formula": "O2",
      "bounds": [-10, 100]
    },
    {
      "id": "cpd00001",
      "name": "H2O",
      "formula": "H2O",
      "bounds": [-100, 100]
    },
    {
      "id": "cpd00009",
      "name": "Phosphate",
      "formula": "HO4P",
      "bounds": [-100, 100]
    },
    {
      "id": "cpd00013",
      "name": "NH3",
      "formula": "H3N",
      "bounds": [-100, 100]
    },
    {
      "id": "cpd00048",
      "name": "Sulfate",
      "formula": "O4S",
      "bounds": [-100, 100]
    }
  ],
  "num_compounds": 20,
  "media_type": "minimal",
  "default_uptake_rate": 100.0,
  "custom_bounds_applied": 2
}
```

**AI Response to User**:
"I've created a glucose minimal medium (media_20251027_a3f9b2) with 20 essential compounds for E. coli growth. The medium includes:
- D-Glucose (carbon source): limited to 5 mmol/gDW/h uptake
- O2 (electron acceptor): up to 10 mmol/gDW/h for aerobic respiration
- Essential salts: phosphate, sulfate, ammonia for biosynthesis
- Trace metals: iron, magnesium, calcium, etc.

This minimal medium should support aerobic growth via glycolysis and the TCA cycle."

**Key Outputs**:
- **media_id**: "media_20251027_a3f9b2" (stored in session for later use)
- **Human-readable compound list**: Enables LLM to understand media composition

### Step 2: Build Draft Metabolic Model

**User Request**: "Build a metabolic model from my E. coli K-12 protein sequences"

**AI Assistant Reasoning**:
1. E. coli is Gram-negative → use GramNegative template
2. User has protein sequences → use as input
3. MVP offline mode → annotate_with_rast=false
4. Create human-readable model name

**AI Assistant Action** - Call build_model:
```json
{
  "protein_sequences": {
    "prot_0001": "MKLVINLVGNSGLGKSTFTQRLINVLFGIDFKRSKTTGGGVWVWNAAETSSYSQYLATFTTGE...",
    "prot_0002": "MKQHKAMIVALERFRKEKRDAALLKDLVKGKRQEVHEVKIEREQEKTALEREKIKEEMKALLK...",
    "prot_0003": "MSVALERYGIDEVASIGGLVEVNN...",
    ...
  },
  "template": "GramNegative",
  "model_name": "E_coli_K12_draft",
  "annotate_with_rast": false
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1",
  "model_name": "E_coli_K12_draft",
  "num_reactions": 856,
  "num_metabolites": 742,
  "num_genes": 150,
  "num_exchange_reactions": 95,
  "template_used": "GramNegative",
  "has_biomass_reaction": true,
  "biomass_reaction_id": "bio1",
  "compartments": ["c0", "e0", "p0"],
  "has_atpm": true,
  "atpm_reaction_id": "ATPM_c0",
  "statistics": {
    "reactions_by_compartment": {
      "c0": 715,
      "e0": 95,
      "p0": 46
    },
    "metabolites_by_compartment": {
      "c0": 580,
      "e0": 95,
      "p0": 67
    },
    "reversible_reactions": 412,
    "irreversible_reactions": 444,
    "transport_reactions": 78
  },
  "model_properties": {
    "is_draft": true,
    "requires_gapfilling": true,
    "estimated_growth_without_gapfilling": 0.0
  }
}
```

**AI Response to User**:
"I've built a draft metabolic model (model_20251027_b4k8c1) for E. coli K-12 using the GramNegative template. Model statistics:
- 856 reactions across 3 compartments (cytosol, extracellular, periplasm)
- 742 metabolites
- 150 genes from your protein sequences
- 95 exchange reactions for nutrient uptake/secretion
- Biomass reaction (bio1) for growth prediction
- ATPM reaction for ATP maintenance energy

⚠️ This is a draft model that typically cannot grow without gapfilling. The template matching identified reactions based on your protein sequences, but some biosynthetic pathways are likely incomplete. I'll need to gapfill the model in the next step."

**Key Outputs**:
- **model_id**: "model_20251027_b4k8c1" (stored in session)
- **Draft model flag**: is_draft=true, requires_gapfilling=true
- **Model statistics**: Help LLM understand model composition

### Step 3: Gapfill Model for Growth in Glucose Medium

**User Request**: "Gapfill the model so it can grow in the glucose minimal medium"

**AI Assistant Reasoning**:
1. Use draft model_id from Step 2
2. Use media_id from Step 1
3. Target minimal growth rate: 0.01 (permissive)
4. Full gapfilling mode (ATP correction + genome-scale)

**AI Assistant Action** - Call gapfill_model:
```json
{
  "model_id": "model_20251027_b4k8c1",
  "media_id": "media_20251027_a3f9b2",
  "target_growth_rate": 0.01,
  "gapfill_mode": "full"
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.gf",
  "original_model_id": "model_20251027_b4k8c1",
  "media_id": "media_20251027_a3f9b2",
  "growth_rate_before": 0.0,
  "growth_rate_after": 0.874,
  "target_growth_rate": 0.01,
  "gapfilling_successful": true,
  "num_reactions_added": 4,
  "reactions_added": [
    {
      "id": "rxn05459_c0",
      "name": "Shikimate kinase",
      "equation": "cpd00036[c0] + cpd00038[c0] => cpd00126[c0] + cpd00008[c0]",
      "direction": "forward",
      "compartment": "c0",
      "source": "template_gapfill"
    },
    {
      "id": "rxn05481_c0",
      "name": "3-dehydroquinate synthase",
      "equation": "cpd00126[c0] => cpd00309[c0] + cpd00009[c0]",
      "direction": "reverse",
      "compartment": "c0",
      "source": "template_gapfill"
    },
    {
      "id": "rxn00599_c0",
      "name": "Chorismate synthase",
      "equation": "cpd00309[c0] => cpd00117[c0] + cpd00009[c0]",
      "direction": "forward",
      "compartment": "c0",
      "source": "template_gapfill"
    },
    {
      "id": "rxn02185_c0",
      "name": "Anthranilate synthase",
      "equation": "cpd00117[c0] + cpd00001[c0] => cpd00056[c0] + cpd00011[c0]",
      "direction": "reverse",
      "compartment": "c0",
      "source": "template_gapfill"
    }
  ],
  "exchange_reactions_added": [
    {
      "id": "EX_cpd01981_e0",
      "name": "Exchange for cpd01981",
      "metabolite": "cpd01981",
      "metabolite_name": "Unknown compound",
      "source": "auto_generated"
    }
  ],
  "atp_correction": {
    "performed": true,
    "media_tested": 54,
    "media_passed": 54,
    "media_failed": 0,
    "reactions_added": 0
  },
  "genomescale_gapfill": {
    "performed": true,
    "reactions_added": 4,
    "reversed_reactions": 0,
    "new_reactions": 4
  },
  "model_properties": {
    "num_reactions": 860,
    "num_metabolites": 743,
    "is_draft": false,
    "requires_further_gapfilling": false
  }
}
```

**AI Response to User**:
"✅ Gapfilling successful! Your E. coli model (model_20251027_b4k8c1.gf) can now grow in glucose minimal medium.

**Gapfilling Results**:
- **Growth rate**: Increased from 0.0 to 0.874 hr⁻¹ (exceeds target of 0.01)
- **Reactions added**: 4 reactions from the shikimate/chorismate biosynthesis pathway
- **ATP correction**: Passed all 54 test media without additional reactions (ATP metabolism is complete)

**Added Reactions** (to enable growth):
1. **Shikimate kinase** (rxn05459_c0): Phosphorylates shikimate in aromatic amino acid biosynthesis
2. **3-dehydroquinate synthase** (rxn05481_c0): Early step in shikimate pathway
3. **Chorismate synthase** (rxn00599_c0): Produces chorismate, a key aromatic precursor
4. **Anthranilate synthase** (rxn02185_c0): Converts chorismate to anthranilate (tryptophan biosynthesis)

**Pathway Interpretation**:
The draft model was missing reactions in aromatic amino acid biosynthesis. Specifically, the shikimate pathway (which produces phenylalanine, tyrosine, and tryptophan) had gaps. These amino acids are essential biomass components, so their synthesis is required for growth. Gapfilling identified and added the minimal set of 4 reactions to complete this pathway.

The model is now ready for flux balance analysis!"

**Key Outputs**:
- **Gapfilled model_id**: "model_20251027_b4k8c1.gf" (stored in session)
- **Growth rate after**: 0.874 hr⁻¹ (can grow)
- **Added reactions with names**: Human-readable pathway information
- **ATP correction success**: No additional reactions needed for energy metabolism

### Step 4: Run Flux Balance Analysis

**User Request**: "Predict the growth rate and show me which metabolic pathways are active"

**AI Assistant Reasoning**:
1. Use gapfilled model from Step 3
2. Use glucose minimal medium from Step 1
3. Default objective (bio1) for growth
4. Default flux threshold to filter noise

**AI Assistant Action** - Call run_fba:
```json
{
  "model_id": "model_20251027_b4k8c1.gf",
  "media_id": "media_20251027_a3f9b2"
}
```

**Response**:
```json
{
  "success": true,
  "model_id": "model_20251027_b4k8c1.gf",
  "media_id": "media_20251027_a3f9b2",
  "objective_reaction": "bio1",
  "objective_value": 0.874,
  "status": "optimal",
  "solver_status": "optimal",
  "active_reactions": 423,
  "total_reactions": 860,
  "total_flux": 2841.5,
  "fluxes": {
    "bio1": 0.874,
    "EX_cpd00027_e0": -5.0,
    "EX_cpd00007_e0": -10.234,
    "EX_cpd00011_e0": 8.456,
    "EX_cpd00001_e0": -15.2,
    "EX_cpd00013_e0": -2.145,
    "EX_cpd00009_e0": -0.876,
    "rxn00148_c0": 5.0,
    "rxn00200_c0": 4.123,
    "rxn00209_c0": 4.871,
    "rxn00216_c0": 3.456,
    "rxn00351_c0": 8.234,
    "rxn00512_c0": 10.456,
    "rxn00086_c0": 3.123
  },
  "uptake_fluxes": [
    {
      "compound_id": "cpd00001",
      "compound_name": "H2O",
      "formula": "H2O",
      "flux": -15.2,
      "reaction_id": "EX_cpd00001_e0"
    },
    {
      "compound_id": "cpd00007",
      "compound_name": "O2",
      "formula": "O2",
      "flux": -10.234,
      "reaction_id": "EX_cpd00007_e0"
    },
    {
      "compound_id": "cpd00027",
      "compound_name": "D-Glucose",
      "formula": "C6H12O6",
      "flux": -5.0,
      "reaction_id": "EX_cpd00027_e0"
    },
    {
      "compound_id": "cpd00013",
      "compound_name": "NH3",
      "formula": "H3N",
      "flux": -2.145,
      "reaction_id": "EX_cpd00013_e0"
    },
    {
      "compound_id": "cpd00009",
      "compound_name": "Phosphate",
      "formula": "HO4P",
      "flux": -0.876,
      "reaction_id": "EX_cpd00009_e0"
    }
  ],
  "secretion_fluxes": [
    {
      "compound_id": "cpd00011",
      "compound_name": "CO2",
      "formula": "CO2",
      "flux": 8.456,
      "reaction_id": "EX_cpd00011_e0"
    }
  ],
  "summary": {
    "uptake_reactions": 15,
    "secretion_reactions": 8,
    "internal_reactions": 400,
    "reversible_active": 150,
    "irreversible_active": 273
  },
  "top_fluxes": [
    {
      "reaction_id": "EX_cpd00001_e0",
      "reaction_name": "H2O exchange",
      "flux": -15.2,
      "direction": "reverse"
    },
    {
      "reaction_id": "rxn00512_c0",
      "reaction_name": "NADH dehydrogenase",
      "flux": 10.456,
      "direction": "forward"
    },
    {
      "reaction_id": "EX_cpd00007_e0",
      "reaction_name": "O2 exchange",
      "flux": -10.234,
      "direction": "reverse"
    },
    {
      "reaction_id": "EX_cpd00011_e0",
      "reaction_name": "CO2 exchange",
      "flux": 8.456,
      "direction": "forward"
    },
    {
      "reaction_id": "rxn00351_c0",
      "reaction_name": "Cytochrome oxidase",
      "flux": 8.234,
      "direction": "forward"
    },
    {
      "reaction_id": "rxn00148_c0",
      "reaction_name": "Hexokinase",
      "flux": 5.0,
      "direction": "forward"
    },
    {
      "reaction_id": "EX_cpd00027_e0",
      "reaction_name": "D-Glucose exchange",
      "flux": -5.0,
      "direction": "reverse"
    },
    {
      "reaction_id": "rxn00209_c0",
      "reaction_name": "Phosphoglucose isomerase",
      "flux": 4.871,
      "direction": "forward"
    },
    {
      "reaction_id": "rxn00216_c0",
      "reaction_name": "Phosphofructokinase",
      "flux": 3.456,
      "direction": "forward"
    },
    {
      "reaction_id": "rxn00200_c0",
      "reaction_name": "Pyruvate dehydrogenase",
      "flux": 4.123,
      "direction": "forward"
    }
  ]
}
```

**AI Response to User (Part 1 - Growth Summary)**:
"✅ Flux Balance Analysis Complete!

**Growth Prediction**:
- **Growth rate**: 0.874 hr⁻¹ (doubling time: ~47 minutes)
- **Optimization status**: Optimal solution found
- **Active reactions**: 423 out of 860 (49% of model)
- **Total metabolic flux**: 2841.5 mmol/gDW/h

**Nutrient Consumption** (Uptake):
1. **H2O** (water): 15.2 mmol/gDW/h - Used in hydrolysis reactions and biosynthesis
2. **O2** (oxygen): 10.2 mmol/gDW/h - Electron acceptor for aerobic respiration
3. **D-Glucose**: 5.0 mmol/gDW/h - Primary carbon and energy source (as limited in medium)
4. **NH3** (ammonia): 2.1 mmol/gDW/h - Nitrogen source for amino acids and nucleotides
5. **Phosphate**: 0.9 mmol/gDW/h - Required for nucleotides, phospholipids, and ATP

**Metabolic Products** (Secretion):
1. **CO2** (carbon dioxide): 8.5 mmol/gDW/h - Complete oxidation of glucose via TCA cycle

The high CO2 production relative to glucose consumption (8.5 / 5.0 = 1.7 CO2 per glucose) indicates efficient aerobic respiration with complete oxidation."

**AI Response to User (Part 2 - Pathway Analysis)**:
"**Most Active Metabolic Pathways**:

1. **Glycolysis** (Glucose → Pyruvate):
   - Hexokinase (rxn00148_c0): 5.0 mmol/gDW/h - Phosphorylates glucose to G6P
   - Phosphoglucose isomerase (rxn00209_c0): 4.9 mmol/gDW/h - G6P → F6P
   - Phosphofructokinase (rxn00216_c0): 3.5 mmol/gDW/h - Rate-limiting step (F6P → F1,6BP)
   - All glucose is entering glycolysis for ATP production and biosynthetic precursors

2. **TCA Cycle** (Aerobic Respiration):
   - Pyruvate dehydrogenase (rxn00200_c0): 4.1 mmol/gDW/h - Pyruvate → Acetyl-CoA
   - High flux indicates pyruvate is being oxidized aerobically (not fermented)
   - TCA cycle generates NADH and FADH2 for electron transport

3. **Electron Transport Chain** (ATP Generation):
   - NADH dehydrogenase (rxn00512_c0): 10.5 mmol/gDW/h - Complex I, oxidizes NADH
   - Cytochrome oxidase (rxn00351_c0): 8.2 mmol/gDW/h - Complex IV, reduces O2 to H2O
   - These are the highest internal fluxes, showing active oxidative phosphorylation
   - The model is generating ATP efficiently through respiration (not fermentation)

**Metabolic Interpretation**:
Your E. coli model is using classic aerobic glucose metabolism:
- Glucose → (Glycolysis) → Pyruvate
- Pyruvate → (TCA cycle) → CO2 + NADH/FADH2
- NADH/FADH2 → (ETC) → ATP + H2O

The high growth rate (0.874 hr⁻¹) and complete oxidation to CO2 are characteristic of efficient aerobic respiration. No fermentation products (ethanol, acetate) are secreted, confirming the model is using oxygen as the terminal electron acceptor."

**Key Outputs**:
- **Optimal growth rate**: 0.874 hr⁻¹
- **Uptake/secretion with names**: Human-readable metabolite list
- **Top fluxes with names**: Identifies most active pathways
- **Active reaction count**: 423 (49% of model active)

### Step 5: Interpret Specific Reactions (Using Database Tools)

**User Follow-up**: "What exactly does the shikimate kinase reaction do? And what is cpd00036?"

**AI Assistant Reasoning**:
1. User wants details on rxn05459_c0 (shikimate kinase)
2. User wants to know what cpd00036 is
3. Use database lookup tools for detailed information

**AI Assistant Action 1** - Call get_reaction_name:
```json
{
  "reaction_id": "rxn05459"
}
```

**Response 1**:
```json
{
  "success": true,
  "id": "rxn05459",
  "name": "Shikimate kinase",
  "abbreviation": "SHKK",
  "equation": "ATP + Shikimate <=> ADP + Shikimate-3-phosphate",
  "equation_compound_ids": "cpd00002 + cpd00036 <=> cpd00008 + cpd00126",
  "reversibility": "reversible",
  "ec_numbers": ["2.7.1.71"],
  "pathways": ["Phenylalanine, tyrosine and tryptophan biosynthesis"],
  "definition": "Catalyzes the phosphorylation of shikimate to produce shikimate-3-phosphate, using ATP as the phosphate donor. Part of the shikimate pathway for aromatic amino acid biosynthesis."
}
```

**AI Assistant Action 2** - Call get_compound_name:
```json
{
  "compound_id": "cpd00036"
}
```

**Response 2**:
```json
{
  "success": true,
  "id": "cpd00036",
  "name": "Shikimate",
  "abbreviation": "shikimate",
  "formula": "C7H10O5",
  "charge": 0,
  "mass": 174.15,
  "aliases": ["shikimic acid", "3,4,5-trihydroxy-1-cyclohexene-1-carboxylic acid"]
}
```

**AI Assistant Action 3** - Call get_compound_name for ATP:
```json
{
  "compound_id": "cpd00002"
}
```

**Response 3**:
```json
{
  "success": true,
  "id": "cpd00002",
  "name": "ATP",
  "abbreviation": "atp",
  "formula": "C10H16N5O13P3",
  "charge": -4,
  "aliases": ["adenosine triphosphate", "adenosine-5'-triphosphate"]
}
```

**AI Response to User**:
"**Shikimate Kinase (rxn05459)** - EC 2.7.1.71

**Reaction**:
```
ATP + Shikimate → ADP + Shikimate-3-phosphate
```

**What it does**:
Shikimate kinase phosphorylates shikimate (cpd00036) to produce shikimate-3-phosphate (cpd00126) by transferring a phosphate group from ATP. This is the 5th step in the shikimate pathway.

**Compound Details**:
- **Shikimate** (cpd00036): C7H10O5 - An intermediate in the biosynthesis of aromatic amino acids (phenylalanine, tyrosine, tryptophan). Also known as shikimic acid.
- **ATP** (cpd00002): C10H16N5O13P3 - Adenosine triphosphate, the universal energy currency

**Biological Context**:
The shikimate pathway is essential for bacteria, plants, and fungi (but absent in animals). It produces chorismate, which is the precursor for:
1. **Phenylalanine** - Essential aromatic amino acid
2. **Tyrosine** - Essential aromatic amino acid
3. **Tryptophan** - Essential aromatic amino acid

These amino acids are required components of the biomass reaction. Without this pathway, the cell cannot synthesize proteins and therefore cannot grow. This is why the gapfilling algorithm identified this reaction as essential - your draft model was missing this step, preventing aromatic amino acid synthesis."

**Key Functionality**:
- Database lookups provide detailed reaction mechanisms
- Compound formulas and aliases help with interpretation
- Pathway context explains biological significance
- EC numbers enable literature lookup

## Workflow Variations

### Variation 1: Anaerobic Conditions

**User Request**: "How would growth differ under anaerobic conditions?"

**Modified Workflow**:
1. **Step 1 Modified** - Create anaerobic medium:
   ```json
   {
     "compounds": ["cpd00027", "cpd00007", ...],
     "custom_bounds": {
       "cpd00027": [-5, 100],
       "cpd00007": [0, 0]  // Block oxygen
     }
   }
   ```

2. **Steps 2-3** - Same (build and gapfill model)

3. **Step 4** - Run FBA with anaerobic medium:
   ```json
   {
     "model_id": "model_20251027_b4k8c1.gf",
     "media_id": "media_anaerobic"
   }
   ```

**Expected Results**:
- Lower growth rate (~0.2-0.3 hr⁻¹)
- Higher glucose uptake (less efficient)
- Fermentation products: ethanol, acetate, formate
- Different pathway usage: fermentation instead of respiration

### Variation 2: Rich Media (LB-type)

**User Request**: "Compare growth in rich medium vs minimal medium"

**Modified Workflow**:
1. **Step 1 Modified** - Create rich medium with 100+ compounds:
   ```json
   {
     "compounds": [
       "cpd00027", "cpd00007", ...amino acids..., ...vitamins..., ...nucleotides...
     ],
     "default_uptake": 100.0  // No restrictions
   }
   ```

2. **Steps 2-4** - Same workflow

**Expected Results**:
- Higher growth rate (~1.0-1.2 hr⁻¹)
- Lower biosynthetic pathway flux (use nutrients instead of synthesis)
- More uptake reactions active
- Reduced metabolic burden

### Variation 3: Production Strain (Non-Growth Objective)

**User Request**: "Maximize ethanol production instead of growth"

**Modified Workflow**:
1. **Steps 1-3** - Same (create medium, build, gapfill)

2. **Step 4 Modified** - Run FBA with ethanol objective:
   ```json
   {
     "model_id": "model_20251027_b4k8c1.gf",
     "media_id": "media_anaerobic",
     "objective": "EX_cpd00363_e0",  // Ethanol exchange
     "maximize": true
   }
   ```

**Expected Results**:
- Maximum ethanol secretion flux
- Zero or minimal growth (all resources to production)
- Different pathway usage optimized for ethanol

### Variation 4: Different Organism (Gram-Positive)

**User Request**: "Build a model for Bacillus subtilis"

**Modified Workflow**:
1. **Step 1** - Same (glucose minimal medium)

2. **Step 2 Modified** - Use GramPositive template:
   ```json
   {
     "protein_sequences": {...},
     "template": "GramPositive",
     "model_name": "B_subtilis_168"
   }
   ```

3. **Steps 3-4** - Same workflow

**Expected Results**:
- Different compartments (no periplasm)
- Different reaction set (Gram-positive specific)
- Potentially different gapfilling needs
- Similar growth rate if organism characteristics similar

## Data Flow Throughout Workflow

### Session State Evolution

**After Step 1** (build_media):
```python
session.media = {
  "media_20251027_a3f9b2": <MSMedia object>
}
```

**After Step 2** (build_model):
```python
session.models = {
  "model_20251027_b4k8c1": <COBRApy Model object (draft)>
}
session.media = {
  "media_20251027_a3f9b2": <MSMedia object>
}
```

**After Step 3** (gapfill_model):
```python
session.models = {
  "model_20251027_b4k8c1": <COBRApy Model object (draft)>,
  "model_20251027_b4k8c1.gf": <COBRApy Model object (gapfilled)>
}
session.media = {
  "media_20251027_a3f9b2": <MSMedia object>
}
```

**After Step 4** (run_fba):
```python
# No new session state (FBA is read-only)
# Same models and media remain in session
```

### ID References Throughout Workflow

```
media_id: "media_20251027_a3f9b2"
  ↓
  Used by: gapfill_model, run_fba

model_id: "model_20251027_b4k8c1"
  ↓
  Used by: gapfill_model (input)

model_id_gf: "model_20251027_b4k8c1.gf"
  ↓
  Used by: run_fba
```

### Compound/Reaction IDs Used

**Throughout workflow**:
- ModelSEED IDs in tool inputs/outputs
- Human-readable names in AI responses
- Database lookups bridge the gap

**Example transformations**:
```
"cpd00027" → (database lookup) → "D-Glucose"
"rxn00148" → (database lookup) → "Hexokinase"
```

## Error Handling in Complete Workflow

### Error Scenario 1: Invalid Medium Composition

**Problem**: User creates medium missing essential nutrients

**Step 1**: build_media succeeds (compounds valid)
**Step 3**: gapfill_model fails with "GapfillingInfeasibleError"

**AI Recovery**:
1. Recognize gapfilling failed due to media
2. Analyze which nutrients might be missing
3. Call build_media with more complete medium
4. Retry gapfill_model

### Error Scenario 2: Invalid Protein Sequences

**Problem**: User provides sequences with invalid characters

**Step 2**: build_model fails with "ValidationError"

**AI Recovery**:
1. Identify which sequences have errors
2. Ask user to fix sequences or remove invalid ones
3. Retry build_model with corrected input

### Error Scenario 3: Draft Model FBA

**Problem**: User tries FBA on draft model (skips gapfilling)

**Step 4**: run_fba returns "InfeasibleModelError"

**AI Recovery**:
1. Recognize model needs gapfilling
2. Suggest running gapfill_model first
3. Execute gapfilling workflow
4. Retry FBA on gapfilled model

### Error Scenario 4: Database Lookup Failure

**Problem**: Reaction/compound ID not in database

**Step 5**: get_reaction_name returns "NotFoundError"

**AI Recovery**:
1. Report unknown ID to user
2. Provide whatever information is available from model
3. Suggest this might be a custom/non-standard reaction

## Performance Characteristics

### Expected Execution Times

**Complete workflow timing** (typical E. coli model):
1. **build_media**: < 500ms
2. **build_model**: 10-30 seconds
3. **gapfill_model**: 1-3 minutes
4. **run_fba**: < 200ms
5. **Database lookups**: < 50ms each

**Total workflow time**: 2-4 minutes for typical case

### Performance Bottlenecks

**Slowest operations**:
1. **Gapfilling** (60-80% of total time)
   - ATP correction tests 54 media
   - MILP solving for genome-scale gapfilling
2. **Model building** (15-25% of total time)
   - Template matching
   - Model construction
3. **Other tools** (< 5% of total time)
   - FBA, media creation, lookups all fast

### Optimization Opportunities (Future)

**Not needed for MVP**, but potential future improvements:
- Parallel ATP correction media testing
- Cached gapfilling solutions for similar organisms
- Faster MILP solver (CPLEX vs GLPK)
- Pre-computed template reactions

## Integration Pattern for AI Assistants

### Conversational Flow

**User initiates**: "I want to build a metabolic model"

**AI Gathers information**:
1. "What organism are you modeling?" → Determines template
2. "Do you have protein sequences?" → Validates build_model input
3. "What growth conditions?" → Guides build_media

**AI Executes workflow**:
1. Explains each step before executing
2. Shows progress during long operations (gapfilling)
3. Interprets results in biological terms
4. Anticipates next steps

**AI Handles errors**:
1. Catches errors at each step
2. Explains error in user-friendly terms
3. Suggests fixes or alternative approaches
4. Retries after corrections

### Knowledge Required by AI

**Biological knowledge**:
- Organism types (Gram-negative vs positive)
- Media composition basics (carbon, nitrogen, electron acceptor)
- Metabolic pathways (glycolysis, TCA, fermentation)
- Aerobic vs anaerobic conditions

**System knowledge**:
- Tool sequence (media → model → gapfill → FBA)
- When gapfilling is needed (always for draft models)
- How to interpret FBA results
- Which database lookups are useful

**Error handling knowledge**:
- Common failure modes
- How to recover from errors
- When to ask user for clarification

## Testing Complete Workflow

### Integration Test Case 1: E. coli Aerobic Glucose

**Setup**:
- 150 E. coli protein sequences
- Glucose minimal medium
- Aerobic conditions

**Execute**:
1. build_media → success
2. build_model → success (draft model)
3. gapfill_model → success (4 reactions added)
4. run_fba → success (growth ~0.8-0.9 hr⁻¹)

**Verify**:
- ✅ Model builds successfully
- ✅ Gapfilling achieves growth
- ✅ FBA shows optimal status
- ✅ Uptake includes glucose and O2
- ✅ Secretion includes CO2
- ✅ Growth rate biologically reasonable

### Integration Test Case 2: E. coli Anaerobic Glucose

**Setup**:
- Same model as Test 1
- Glucose minimal medium with O2 blocked

**Execute**:
1. Use model from Test 1
2. build_media (anaerobic) → success
3. run_fba with anaerobic media → success

**Verify**:
- ✅ Lower growth rate than aerobic
- ✅ Fermentation products in secretion
- ✅ No O2 uptake
- ✅ Higher glucose uptake

### Integration Test Case 3: Rich Media Growth

**Setup**:
- Same model as Test 1
- Rich medium with 100+ compounds

**Execute**:
1. build_media (rich) → success
2. run_fba → success

**Verify**:
- ✅ Higher growth rate than minimal
- ✅ More uptake reactions active
- ✅ Lower biosynthetic pathway flux

### Integration Test Case 4: Error Recovery

**Setup**:
- Intentionally create incomplete medium (missing nitrogen)

**Execute**:
1. build_media (incomplete) → success
2. build_model → success
3. gapfill_model → fails (infeasible)
4. Fix medium (add nitrogen)
5. Retry gapfill_model → success

**Verify**:
- ✅ Gapfilling error is clear
- ✅ Suggestion mentions missing nutrients
- ✅ Retry succeeds after fix

## Quality Requirements

### Correctness

- ✅ Each tool produces valid outputs
- ✅ Tools compose correctly (outputs match input requirements)
- ✅ Gapfilled models achieve target growth
- ✅ FBA solutions are mathematically optimal
- ✅ Database lookups return accurate information

### Reliability

- ✅ Workflow completes successfully for valid inputs
- ✅ Errors at any step don't corrupt session state
- ✅ Failed steps can be retried
- ✅ Original models/media preserved after gapfilling

### Usability

- ✅ Each step provides clear progress indication
- ✅ Results include human-readable interpretations
- ✅ Errors suggest recovery actions
- ✅ Biological context helps user understanding

### Performance

- ✅ Complete workflow < 5 minutes typical
- ✅ Long operations (gapfilling) < 10 minutes
- ✅ Fast operations (FBA, lookups) < 1 second

## Related Specifications

- **001-system-overview.md**: System architecture and tool overview
- **003-build-media-tool.md**: Media creation (Step 1)
- **004-build-model-tool.md**: Model building (Step 2)
- **005-gapfill-model-tool.md**: Gapfilling (Step 3)
- **006-run-fba-tool.md**: Flux balance analysis (Step 4)
- **008-compound-lookup-tools.md**: Compound interpretation (Step 5)
- **009-reaction-lookup-tools.md**: Reaction interpretation (Step 5)
- **010-model-storage.md**: Session management throughout
- **011-model-import-export.md**: Alternative model input/output

---

**Document Status**: ✅ Ready for Implementation
**Last Updated**: October 27, 2025
**Next Spec**: 013-error-handling.md
