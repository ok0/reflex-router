# References

This file lists one entry for each work cited in the repository's documentation (the file set of spec R1), plus the related-work works that the study names. It does not list works that are not cited in that file set.

Status legend:
- `verified`: the detail was read on a primary, publisher or index page (PubMed, PMC, Europe PMC, Crossref, DataCite, doi.org landing, arXiv, OpenReview, Zenodo, PyPI, publisher) during M10, on the date given.
- `unverified / 미검증`: the detail was not confirmed in M10.
- Evidence level: `full text`, `abstract only`, `secondary page`, or `none` (no content of the work was read; only bibliographic details were checked).

## Bibliography

### ache2019
- Authors: Ache, Polsky, Alghailani, Parekh, Breads, Peek, Bock, von Reyn, Card (surnames as recorded in the research note; initials not recorded)
- Title: Neural Basis for Looming Size and Velocity Encoding in the Drosophila Giant Fiber Escape Pathway
- Venue and year: Current Biology, 2019
- Volume/pages: 29(6):1073-1081.e4
- Identifiers (DOI / arXiv / URL): DOI 10.1016/j.cub.2019.01.079; PMID 30827912
- Cited in: docs/report.md, docs/report.ko.md
- Verification source: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22von%20Reyn%20CR%22%20AND%20TITLE:%22Feature%20integration%22&format=json&resultType=lite (Europe PMC index)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: Year (2019) and first author (Ache) in `docs/report.md` and `docs/report.ko.md` agree with the index record. Only bibliographic details were checked; the content of the paper (LC4/LPLC2 to giant fiber) was not read in M10.

### chen2023
- Authors: Chen, Zaharia, Zou
- Title: FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance
- Venue and year: arXiv preprint, 2023 (TMLR 2024 venue unverified)
- Volume/pages: not found
- Identifiers (DOI / arXiv / URL): arXiv 2305.05176; https://arxiv.org/abs/2305.05176
- Cited in: README.md (read-only; "FrugalGPT. TMLR 2024")
- Verification source: https://arxiv.org/abs/2305.05176 (arXiv); OpenReview forum https://openreview.net/forum?id=cSimKw5p6R was blocked (browser-check interstitial) and not read
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: abstract only
- Notes: TMLR outcome: "TMLR venue unverified". The OpenReview page was not read, and a web search found no TMLR listing. arXiv v1 only (9 May 2023); no journal reference shown. The README.md claim "TMLR 2024" is therefore not confirmed.

### dean2013
- Authors: Jeffrey Dean, Luiz André Barroso
- Title: The Tail at Scale
- Venue and year: Communications of the ACM, 2013 (February)
- Volume/pages: 56(2):74-80
- Identifiers (DOI / arXiv / URL): DOI 10.1145/2408776.2408794
- Cited in: README.md (read-only; "Dean, Barroso (2013). The Tail at Scale. CACM.")
- Verification source: https://api.crossref.org/works/10.1145/2408776.2408794 (Crossref index)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: Title, venue, volume, pages, DOI and authors agree with README.md. The ACM Digital Library page was not read separately.

### ding2024
- Authors: Ding, Mallick, Wang, Sim, Mukherjee, Ruhle, Lakshmanan, Awadallah (surnames as on the arXiv page per the research note; initials not recorded)
- Title: Hybrid LLM: Cost-Efficient and Quality-Aware Query Routing
- Venue and year: arXiv preprint, 2024; "Accepted to ICLR 2024 (main conference)" per the arXiv comment
- Volume/pages: not found
- Identifiers (DOI / arXiv / URL): arXiv 2404.14618; https://arxiv.org/abs/2404.14618
- Cited in: none (related-work item; not cited in the repository's documentation file set)
- Verification source: https://arxiv.org/abs/2404.14618 (arXiv)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: abstract only
- Notes: The ICLR 2024 proceedings page was not fetched; the venue rests on the arXiv comment only. Headline claim is in `## Related work`.

### dorkenwald2024
- Authors: Dorkenwald et al. (full author list not recorded in the research note; approx. 290 authors plus the FlyWire Consortium)
- Title: Neuronal wiring diagram of an adult brain
- Venue and year: Nature, 2024
- Volume/pages: 634(8032):124-138
- Identifiers (DOI / arXiv / URL): DOI 10.1038/s41586-024-07558-y
- Cited in: README.md, docs/report.md, docs/report.ko.md, circuit-data/NOTICE.md
- Verification source: https://api.crossref.org/works/10.1038/s41586-024-07558-y (Crossref index, landing-page spot check)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: Spot check only, as planned (item e). The LC4/LPLC2-to-giant-fiber analysis in this paper was not checked; `docs/report.md` already marks it unverified.

### eckstein2024
- Authors: Eckstein, N. et al. (first author Nils Eckstein; Crossref lists 23 authors; full list not recorded in the research note)
- Title: Neurotransmitter classification from electron microscopy images at synaptic sites in Drosophila melanogaster
- Venue and year: Cell, 2024 (May; online 22 March 2024)
- Volume/pages: 187(10):2574-2594.e23
- Identifiers (DOI / arXiv / URL): DOI 10.1016/j.cell.2024.03.016
- Cited in: circuit-data/NOTICE.md, circuit-data/v783/metadata.json (`eckstein_bates2024`)
- Verification source: https://api.crossref.org/works/10.1016/j.cell.2024.03.016 (Crossref index)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: DOI outcome: found. The metadata.json entry `eckstein_bates2024` has `doi: null` and `doi_status: "unverified"`; the DOI above is the Crossref record. Bates's co-authorship and position were not read, and it was not checked whether this Cell paper is the work that the repository's "neurotransmitter predictions" citation refers to.

### flyconnectome-annotations
- Authors: not found
- Title: flyconnectome/flywire_annotations (cell-type annotations; tag v3.2.0, dataset/software)
- Venue and year: not found
- Volume/pages: not found
- Identifiers (DOI / arXiv / URL): GitHub repository flyconnectome/flywire_annotations; tag v3.2.0 (not verified)
- Cited in: circuit-data/NOTICE.md
- Verification source: none
- Date consulted: 2026-10-18
- Status: unverified / 미검증
- Evidence level: none
- Notes: Not fetched in M10. The tag v3.2.0 and the tag pinned in `discovery/discovery.toml` were not compared.

### flywirecodingcortex
- Authors: "FlyWire Coding Cortex contributors" (PyPI author field; no individual author recorded)
- Title: flywire-coding-cortex (Python package; summary: "Run FlyWire-derived LIF neurons and map rates to coding-agent drives")
- Venue and year: PyPI package; latest version 0.1.1, uploaded 2026-09-23 (0.1.0 also uploaded 2026-09-23); no paper found
- Volume/pages: not applicable
- Identifiers (DOI / arXiv / URL): PyPI flywire-coding-cortex; repository https://github.com/imrizwan/flywire-cortex (public, 5 commits, no releases)
- Cited in: none (related-work item; not cited in the repository's documentation file set)
- Verification source: https://pypi.org/pypi/flywire-coding-cortex/json (PyPI index); https://github.com/imrizwan/flywire-cortex (README read)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: secondary page
- Notes: Verified: existence, version, upload dates and license (code MIT; the README states that the circuit data is CC BY-NC 4.0). The package is not a peer-reviewed work and no paper or FlyWire Consortium affiliation was found. Its README states that it does not claim biologically calibrated coding skill and reports no benchmark result. Contents beyond the package summary and README were not verified. Listed in `## Related work`.

### flywireconsortium2024
- Authors: FlyWire Consortium
- Title: FlyWire Whole-brain Connectome Connectivity Data
- Venue and year: Zenodo (dataset), 2024 (published 2024-06-02)
- Volume/pages: version 783.0
- Identifiers (DOI / arXiv / URL): DOI 10.5281/zenodo.10676866; https://zenodo.org/records/10676866
- Cited in: circuit-data/NOTICE.md, circuit-data/v783/metadata.json, docs/licensing.md
- Verification source: https://zenodo.org/api/records/10676866 (Zenodo record API)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: The Zenodo record states license `cc-by-4.0`. This matches the statement in circuit-data/NOTICE.md ("Zenodo v783 record states CC BY 4.0"). The conflict with FlyWire Terms of Service and Principles (CC BY-NC 4.0) is recorded in `docs/licensing.md`; this entry does not resolve it.

### lin2023
- Authors: Lin, Fu, Yang, Brahman, Huang, Bhagavatula, Ammanabrolu, Choi, Ren (surnames as on the arXiv page per the research note; initials not recorded)
- Title: SwiftSage: A Generative Agent with Fast and Slow Thinking for Complex Interactive Tasks
- Venue and year: arXiv preprint, 2023; "Accepted to NeurIPS 2023 as a spotlight" per the arXiv comment
- Volume/pages: not found
- Identifiers (DOI / arXiv / URL): arXiv 2305.17390; https://arxiv.org/abs/2305.17390
- Cited in: none (related-work item; not cited in the repository's documentation file set)
- Verification source: https://arxiv.org/abs/2305.17390 (arXiv, v2)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: abstract only
- Notes: The NeurIPS 2023 proceedings page was not fetched; the venue rests on the arXiv comment only. Headline claim is in `## Related work`.

### matsliah2023
- Authors: Matsliah, Sterling, Dorkenwald, Kuehner, Morey, Seung, Murthy (surnames as recorded on DataCite per the research note)
- Title: Codex: Connectome Data Explorer
- Venue and year: Preprint, 2023; publisher "Unpublished" (DataCite)
- Volume/pages: not found
- Identifiers (DOI / arXiv / URL): DOI 10.13140/RG.2.2.35928.67844 (the DOI resolves to a ResearchGate record)
- Cited in: circuit-data/NOTICE.md
- Verification source: https://api.datacite.org/dois/10.13140/rg.2.2.35928.67844 (DataCite index); doi.org redirect to ResearchGate
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: The DataCite record gives title, creators, year and type (preprint); no description is given. The Codex content was not read, and the DOI is not a journal citation.

### ong2024
- Authors: Ong, Almahairi, Wu, Chiang, T. Wu, Gonzalez, Kadous, Stoica
- Title: RouteLLM: Learning to Route LLMs from Preference Data (ICLR 2025 proceedings title); arXiv title: RouteLLM: Learning to Route LLMs with Preference Data
- Venue and year: ICLR 2025 (proceedings); arXiv preprint 2024
- Volume/pages: not found
- Identifiers (DOI / arXiv / URL): arXiv 2406.18665; https://arxiv.org/abs/2406.18665; ICLR 2025 proceedings: https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html
- Cited in: none (related-work item; not cited in the repository's documentation file set)
- Verification source: https://arxiv.org/abs/2406.18665 (arXiv, v4); ICLR 2025 proceedings page (listed above)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: abstract only
- Notes: Title difference: arXiv says "with Preference Data"; the ICLR 2025 proceedings page says "from Preference Data". The ICLR title is used as the venue title; the arXiv title is recorded here. Proceedings page numbers were not found.

### schlegel2024
- Authors: Schlegel, P. et al. (first authors Philipp Schlegel, Yijie Yin, Alexander S. Bates; about 300 author entries including the FlyWire Consortium; full list not recorded)
- Title: Whole-brain annotation and multi-connectome cell typing of Drosophila (Nature). The bioRxiv preprint (doi 10.1101/2023.06.27.546055) has the title "Whole-brain annotation and multi-connectome cell typing quantifies circuit stereotypy in Drosophila".
- Venue and year: Nature, 2024 (online 2 October 2024); bioRxiv preprint, 2023
- Volume/pages: Nature 634:139-152
- Identifiers (DOI / arXiv / URL): Nature DOI 10.1038/s41586-024-07686-5; preprint DOI 10.1101/2023.06.27.546055 (Europe PMC PPR682134)
- Cited in: docs/report.md, docs/report.ko.md, circuit-data/NOTICE.md, discovery/README.md
- Verification source: https://api.crossref.org/works/10.1038/s41586-024-07686-5 (Crossref index, Nature metadata); https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1101/2023.06.27.546055%22&format=json&resultType=core (Europe PMC, preprint abstract). The nature.com page redirected to a login and was not read; bioRxiv full text returned HTTP 429 and was not read.
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: abstract only
- Notes: Filter wording location: `preprint abstract`. The bioRxiv abstract says connections "stronger than 10 unitary synapses" and providing ">1% of the input to a target cell". The exact phrase "more than 10 synapses or 1% of target input" is not verbatim in that abstract. The Nature paper was not read (login redirect), and the preprint full text was not read (HTTP 429). Whether the wording also appears in those texts is unknown (not checked; not "absent"). Preprint title differs from the Nature title.

### shiu2024
- Authors: Shiu, Sterne, Spiller, Franconville, Sandoval, Zhou, Simha, Kang, S. Yu, J. S. Kim, Dorkenwald, Matsliah, Schlegel, Sz. Yu, McKellar, Sterling, Costa, Eichler, Bates, Eckstein, Funke, Jefferis, Murthy, Bidaye, Hampel, Seeds, Scott (27 authors; initials other than those shown were not recorded)
- Title: A Drosophila computational brain model reveals sensorimotor processing
- Venue and year: Nature, 2024 (online 2 October 2024)
- Volume/pages: 634(8032):210-219
- Identifiers (DOI / arXiv / URL): DOI 10.1038/s41586-024-07763-9
- Cited in: docs/report.md, docs/report.ko.md, docs/licensing.md, circuit-data/NOTICE.md, discovery/README.md
- Verification source: https://api.crossref.org/works/10.1038/s41586-024-07763-9 (Crossref index)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: Author-list outcome: the full 27-author list is verified on the Crossref record, in the order given in the research note (matches the earlier bibliography check). The Nature and PMC (PMC11446845) pages were not re-read. The Shiu methods were read from the preprint (see `docs/report.md`), which this entry does not change.

### shiu2024code
- Authors: not verified in M10 (the repository owner is `philshiu`; the copyright line in the vendored LICENSE names Philip Shiu and Nico Spiller and was not read in M10)
- Title: philshiu/Drosophila_brain_model (code)
- Venue and year: GitHub repository; year not found
- Volume/pages: not applicable
- Identifiers (DOI / arXiv / URL): https://github.com/philshiu/Drosophila_brain_model; commit 91bdd1e7dcf193f3e7ca5a8933497fcef63b7960 (as pinned in discovery/README.md)
- Cited in: circuit-data/NOTICE.md, discovery/README.md, docs/licensing.md
- Verification source: none
- Date consulted: 2026-10-18
- Status: unverified / 미검증
- Evidence level: none
- Notes: The commit 91bdd1e7... was not fetched, and the MIT license of the upstream repository was not checked in M10. Vendored files are described in `docs/licensing.md`.

### vonreyn2014
- Authors: von Reyn, C. R. et al. (first author von Reyn CR; other authors not recorded)
- Title: A spike-timing mechanism for action selection
- Venue and year: Nature Neuroscience, 2014
- Volume/pages: 17(7):962-970
- Identifiers (DOI / arXiv / URL): DOI 10.1038/nn.3741; PMID 24908103
- Cited in: README.md (read-only), docs/report.md, docs/report.ko.md
- Verification source: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22von%20Reyn%20CR%22%20AND%20(TITLE:%22spike-timing%22%20OR%20TITLE:%22looming%22%20OR%20TITLE:%22visual%20projection%22)&format=json&resultType=lite (Europe PMC index)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: Year and first author agree with `docs/report.md` and `docs/report.ko.md`. Title and journal agree with README.md. Only bibliographic details were checked; the content (threshold and route claims) was not read in M10.

### vonreyn2017
- Authors: von Reyn, Nern, Williamson, Breads, Wu, Namiki, Card (surnames as recorded in the research note; initials not recorded)
- Title: Feature Integration Drives Probabilistic Behavior in the Drosophila Escape Response
- Venue and year: Neuron, 2017
- Volume/pages: 94(6):1190-1204.e6
- Identifiers (DOI / arXiv / URL): DOI 10.1016/j.neuron.2017.05.036; PMID 28641115
- Cited in: docs/report.md, docs/report.ko.md
- Verification source: https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22von%20Reyn%20CR%22%20AND%20TITLE:%22Feature%20integration%22&format=json&resultType=lite (Europe PMC index)
- Date consulted: 2026-10-18
- Status: verified
- Evidence level: none
- Notes: Year and first author agree with `docs/report.md` and `docs/report.ko.md`. Only bibliographic details were checked; the content (LC4/LPLC2 to giant fiber) was not read in M10.

## Related work

FrugalGPT (Chen, Zaharia and Zou, arXiv 2305.05176) is a study of using LLMs while reducing cost. Its abstract states that FrugalGPT can match the performance of the best individual LLM (for example GPT-4) with up to 98% cost reduction (self-reported by the authors, not reproduced here). Its TMLR 2024 venue is unverified.

RouteLLM (Ong et al., ICLR 2025; arXiv 2406.18665) trains routers on preference data to choose between a stronger and a weaker LLM at inference. Its abstract reports cost reductions of over 2x in some cases without loss in response quality (self-reported by the authors, not reproduced here).

Hybrid LLM (Ding et al., ICLR 2024 per the arXiv comment; arXiv 2404.14618) routes each query to a small or a large model based on predicted difficulty, with a quality level adjustable at test time. Its abstract reports up to 40% fewer calls to the large model with no drop in response quality (self-reported by the authors, not reproduced here).

SwiftSage (Lin et al., NeurIPS 2023 per the arXiv comment; arXiv 2305.17390) is a generative agent with fast and slow thinking for interactive tasks. Its abstract reports that on 30 ScienceWorld tasks it significantly outperforms other methods such as SayCan, ReAct and Reflexion (self-reported by the authors, not reproduced here).

flywire-coding-cortex is a PyPI package (latest version 0.1.1; summary: "Run FlyWire-derived LIF neurons and map rates to coding-agent drives") (self-reported by the authors, not reproduced here). Its README states that it does not claim biologically calibrated coding skill and reports no benchmark result. No paper was found, and its contents beyond the package summary and README are unverified / 미검증.

This study does not compare its results with these works.
