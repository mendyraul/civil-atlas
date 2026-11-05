# Remaining 117 CE identity review

Checked November 5, 2026. This is a review dossier for the seven unmapped rows
in `backend/data/imports/crosswalks/cliopatria-117-inventory.json`. It proposes
identities and records the questions that prevent automatic matching. It does
not approve historical records, alter source geometry or add crosswalk entries.

## Source IDs and proposed identities

Cliopatria identifiers are source-local lookup keys. A row's name, date interval
and geometry must also be considered. Its QID must not silently become the
canonical Wikidata identity used by OHM or the enrichment importer. The existing
Roman mapping illustrates this: Cliopatria uses Q12544 for its Roman Empire row,
while the canonical Roman Empire item is Q2277.

The inventory's `identity_review` objects retain revision-pinned Wikidata links,
the SHA-256 of each inspected entity response, proposed targets and a specific
remaining decision. Proposed QIDs are references for review, not active aliases.
The source archive and original row properties remain unchanged.

| Source row (interval containing 117 CE) | Finding | Proposed next action |
| --- | --- | --- |
| Hadhramaut, Q1517159 (-350–183) | The source QID identifies the geographic region. Q369778 identifies the ancient Kingdom of Hadhramaut. | Review a source-local match to a separate `kingdom-of-hadhramaut` candidate; retain Q1517159 in the original source record. |
| Dongye, Q105946539 (-36–312) | The source QID identifies a disambiguation page. Q713397 identifies the historical Dongye state. | Review a name-checked, source-local correction to a `dongye` candidate with canonical Q713397. |
| Dong-okjeo, Q713393 (43–126) | Q713393 identifies broader Okjeo. Eastern and Northern Okjeo have distinct geographic scopes. | Preserve `dong-okjeo` as the narrower source identity if added; do not make it an exact alias of all Okjeo. |
| Goths, Q42193 (43–153) | The item identifies a people; this does not establish a single territorial state in 117. | Decide whether this belongs in a cultural/people layer or can support an explicitly source-reported polity candidate. |
| Anurādhapura, Q5724 (78–438) | The source QID identifies the city. Q1965597 identifies the Anuradhapura Kingdom. | Review a source-local kingdom match to `anuradhapura-kingdom`; retain a separate city/place identity. |
| Huns, Q45813 (106–370) | The item identifies a people. The unusually early source interval also requires a chronology check. | Keep excluded from the 117 polity seed until a cited interpretation explains the row's identity and location; do not substitute Xiongnu. |
| Teotihuacan, Q172613 (106–655) | The item identifies the ancient city. Urban existence does not validate the source polygon as a territorial state. | Decide whether to model a city/place, an urban polity or both, and review the territorial claim separately. |

## Evidence and limits

For Hadhramaut, the [Yemeni state's tentative-list submission hosted by
UNESCO](https://whc.unesco.org/en/tentativelists/6855) describes an ancient kingdom
and its capital. That supports distinguishing the kingdom from the modern region.
The proposed source-row match is still an inference; the submission does not
validate the Cliopatria polygon or its exact interval. It is a state submission,
not a UNESCO boundary endorsement.

For Dongye, the distinct [historical-state item
Q713397](https://www.wikidata.org/w/index.php?title=Q713397&oldid=2225428090)
resolves the obvious disambiguation-page error at the identifier level. The
[National Geographic Information Institute's historical
overview](https://nationalatlas.ngii.go.kr/pages/page_1938.php) also distinguishes
Dongye and Okjeo. Neither source certifies the imported frontier.

For Dong-okjeo, the [Academy of Korean Studies' Okjeo
entry](https://encykorea.aks.ac.kr/Article/E0038760) distinguishes Eastern Okjeo
around Hamhung from Northern Okjeo around the Tumen River. The [National Institute
of Korean History's source
reader](https://contents.history.go.kr/mobile/hm/view.do?levelId=hm_003_0040)
provides the relevant historical text and interpretation. This supports retaining
the narrower source name, rather than asserting exact equivalence with broader
Okjeo or independent sovereignty throughout 43–126.

For Anuradhapura, [Sri Lanka Tourism's heritage
overview](https://srilanka.travel/heritage-discover-the-past?article=29) distinguishes
the city and the kingdom named for it. [UNESCO's city
entry](https://whc.unesco.org/en/list/200/) describes its role as a capital. These
support separate city and kingdom identities, without establishing the imported
extent or its 78–438 interval.

For Goths, the [inspected Wikidata
item](https://www.wikidata.org/w/index.php?title=Q42193&oldid=2547162320) classifies
the subject as an ethnolinguistic group. This classification alone cannot decide
whether the atlas should include a source-reported territorial reading under its
civilization model. A cultural identity must not acquire a sovereign-state claim
merely because the upstream file labels its row `POLITY`.

For Huns, [Encyclopaedia Iranica's Huns
article](https://www.iranicaonline.org/articles/huns/) discusses both early
attestations and the difficulty of identifying different groups called Huns.
Its [Xiongnu article](https://www.iranicaonline.org/articles/xiongnu/) cautions
against inferring descent or equivalence from names. This is a reason to review
the 117 reading, not proof that every early attestation is false. Keep Huns and
the separately imported Xiongnu identity distinct.

For Teotihuacan, [UNESCO's site
entry](https://whc.unesco.org/en/list/414/) establishes an ancient city with broad
regional influence. The [Metropolitan Museum's archaeological
overview](https://www.metmuseum.org/essays/teotihuacan-pyramids-of-the-sun-and-the-moon)
provides urban and monumental context. Neither validates the Cliopatria territorial
polygon as a single polity in 117.

These references are citation-only; their prose, images and map geometries have
not been imported into the historical dataset.

## Completion requirements

For each candidate, record the accepted identity and entity type, a cited
interpretation of its 117 CE scope, and the rationale for accepting or excluding
the source row. An exclusion is a documented scope decision, not an unexplained
omission. For an addition, create a private civilization and source-backed claim,
retain original geometry and date qualifiers, add the name-checked source
crosswalk, and assign review. Publication requires the normal editorial decision.

The inventory currently remains 21 private additions and seven unresolved rows.
Issue #57 remains open. None of this establishes parity with the public preview
outside 117 CE, or supplies a reviewed release for #61.
