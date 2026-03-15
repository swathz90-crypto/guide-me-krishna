#!/usr/bin/env python3
"""Generate a sample Bhagavad Gita corpus JSON with 700 verses for testing."""
import json
import sys

# Actual verse counts per chapter in the Bhagavad Gita
CHAPTER_VERSE_COUNTS = [47, 72, 43, 42, 29, 47, 30, 28, 34, 42, 55, 20, 35, 27, 20, 24, 28, 78]

SAMPLE_TRANSLATIONS = [
    "Never was there a time when I did not exist, nor you, nor all these beings; nor will there be any time when we will cease to exist.",
    "The soul is never born nor dies at any time. It has not come into being, does not come into being, and will not come into being. It is unborn, eternal, ever-existing, and primeval.",
    "You have a right to perform your prescribed duties, but you are not entitled to the fruits of your actions. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
    "One who is not disturbed in mind even amidst the threefold miseries or elated when there is happiness, and who is free from attachment, fear and anger, is called a sage of steady mind.",
    "A person who is not disturbed by the incessant flow of desires — that enter like rivers into the ocean, which is ever being filled but is always still — can alone achieve peace, and not the man who strives to satisfy such desires.",
    "Out of compassion for them, I, dwelling in their hearts, destroy with the shining lamp of knowledge the darkness born of ignorance.",
    "Whatever you do, whatever you eat, whatever you offer or give away, and whatever austerities you perform — do that as an offering to Me.",
    "Fix your mind on Me, be devoted to Me, worship Me, bow down to Me. So shall you come to Me. I promise you truly, for you are dear to Me.",
    "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions. Do not fear.",
    "The living entity in the material world carries his different conceptions of life from one body to another as the air carries aromas.",
    "I am the taste of water, the light of the sun and the moon, the syllable om in the Vedic mantras; I am the sound in ether and ability in man.",
    "Among all trees I am the banyan tree, and of the sages among the demigods I am Narada. Of the Gandharvas I am Citraratha, and among perfected beings I am the sage Kapila.",
    "I am the gambling of cheats, and of the splendid I am the splendor. I am victory, I am adventure, and I am the strength of the strong.",
    "This divine energy of Mine, consisting of the three modes of material nature, is difficult to overcome. But those who have surrendered unto Me can easily cross beyond it.",
    "Four kinds of pious men begin to render devotional service unto Me — the distressed, the desirer of wealth, the inquisitive, and he who is searching for knowledge of the Absolute.",
    "I am the source of all spiritual and material worlds. Everything emanates from Me. The wise who perfectly know this engage in My devotional service and worship Me with all their hearts.",
    "The thoughts of My pure devotees dwell in Me, their lives are fully devoted to My service, and they derive great satisfaction and bliss from always enlightening one another and conversing about Me.",
    "To those who are constantly devoted to serving Me with love, I give the understanding by which they can come to Me.",
]

SAMPLE_SANSKRIT = [
    "नासतो विद्यते भावो नाभावो विद्यते सतः",
    "न जायते म्रियते वा कदाचिन्नायं भूत्वा भविता वा न भूयः",
    "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन",
    "दुःखेष्वनुद्विग्नमनाः सुखेषु विगतस्पृहः",
    "आपूर्यमाणमचलप्रतिष्ठं समुद्रमापः प्रविशन्ति यद्वत्",
    "तेषामेवानुकम्पार्थमहमज्ञानजं तमः",
    "यत्करोषि यदश्नासि यज्जुहोषि ददासि यत्",
    "मन्मना भव मद्भक्तो मद्याजी मां नमस्कुरु",
    "सर्वधर्मान्परित्यज्य मामेकं शरणं व्रज",
    "शरीरं यदवाप्नोति यच्चाप्युत्क्रामतीश्वरः",
    "रसोऽहमप्सु कौन्तेय प्रभास्मि शशिसूर्ययोः",
    "अश्वत्थः सर्ववृक्षाणां देवर्षीणां च नारदः",
    "द्यूतं छलयतामस्मि तेजस्तेजस्विनामहम्",
    "दैवी ह्येषा गुणमयी मम माया दुरत्यया",
    "चतुर्विधा भजन्ते मां जनाः सुकृतिनोऽर्जुन",
    "अहं सर्वस्य प्रभवो मत्तः सर्वं प्रवर्तते",
    "मच्चित्ता मद्गतप्राणा बोधयन्तः परस्परम्",
    "तेषां सततयुक्तानां भजतां प्रीतिपूर्वकम्",
]

SAMPLE_TRANSLITERATION = [
    "nāsato vidyate bhāvo nābhāvo vidyate sataḥ",
    "na jāyate mriyate vā kadācin nāyaṁ bhūtvā bhavitā vā na bhūyaḥ",
    "karmaṇy-evādhikāras te mā phaleṣu kadācana",
    "duḥkheṣv-anudvigna-manāḥ sukheṣu vigata-spṛhaḥ",
    "āpūryamāṇam acala-pratiṣṭhaṁ samudram āpaḥ praviśanti yadvat",
    "teṣām evānukampārtham aham ajñāna-jaṁ tamaḥ",
    "yat karoṣi yad aśnāsi yaj juhoṣi dadāsi yat",
    "man-manā bhava mad-bhakto mad-yājī māṁ namaskuru",
    "sarva-dharmān parityajya mām ekaṁ śaraṇaṁ vraja",
    "śarīraṁ yad avāpnoti yac cāpy utkrāmatīśvaraḥ",
    "raso 'ham apsu kaunteya prabhāsmi śaśi-sūryayoḥ",
    "aśvatthaḥ sarva-vṛkṣāṇāṁ devarṣīṇāṁ ca nāradaḥ",
    "dyūtaṁ chalayatām asmi tejas tejasvinām aham",
    "daivī hy eṣā guṇa-mayī mama māyā duratyayā",
    "catur-vidhā bhajante māṁ janāḥ sukṛtino 'rjuna",
    "ahaṁ sarvasya prabhavo mattaḥ sarvaṁ pravartate",
    "mac-cittā mad-gata-prāṇā bodhayantaḥ parasparam",
    "teṣāṁ satata-yuktānāṁ bhajatāṁ prīti-pūrvakam",
]

SAMPLE_COMMENTARY = [
    "Krishna explains the eternal nature of the soul to Arjuna, dispelling his grief.",
    "The Atman is beyond birth and death — it is the eternal witness.",
    "This is the foundational teaching of Nishkama Karma — selfless action.",
    "The mark of a Sthitaprajna — one of steady wisdom.",
    "True peace comes from inner stillness, not from satisfying desires.",
    "The Lord's grace destroys the darkness of ignorance in devoted hearts.",
    "All actions offered to the Lord become acts of worship.",
    "The path of Bhakti — pure devotion — leads directly to the Lord.",
    "The ultimate surrender — the culmination of all spiritual paths.",
    "The soul carries its impressions like the wind carries fragrance.",
    "The Lord pervades all of creation as its essence and light.",
    "The Lord's divine manifestations in the natural world.",
    "The Lord is present even in the activities of the world.",
    "Maya — the divine illusion — can only be crossed by surrender.",
    "Four types of seekers who turn to the Lord.",
    "The Lord is the ultimate source of all existence.",
    "The joy of devotees who constantly share the Lord's glories.",
    "The Lord's promise to guide devoted seekers to liberation.",
]


def main():
    verses = []
    verse_global_idx = 0

    for chapter_idx, verse_count in enumerate(CHAPTER_VERSE_COUNTS, start=1):
        for verse_num in range(1, verse_count + 1):
            sample_idx = verse_global_idx % len(SAMPLE_TRANSLATIONS)
            verse = {
                "verseId": f"{chapter_idx}.{verse_num}",
                "chapter": chapter_idx,
                "verse": verse_num,
                "sanskrit": SAMPLE_SANSKRIT[sample_idx],
                "transliteration": SAMPLE_TRANSLITERATION[sample_idx],
                "translation": SAMPLE_TRANSLATIONS[sample_idx],
                "commentary": SAMPLE_COMMENTARY[sample_idx],
            }
            verses.append(verse)
            verse_global_idx += 1

    assert len(verses) == 701, f"Expected 701 verses, got {len(verses)}"

    output_path = "data/gita_corpus.json"
    import os
    os.makedirs("data", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(verses)} verses → {output_path}")


if __name__ == "__main__":
    main()
