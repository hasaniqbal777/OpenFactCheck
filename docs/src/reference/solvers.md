(api-solvers)=

# Solvers

```{eval-rst}
.. currentmodule:: openfactcheck.solvers
```

## Dummy Solvers

```{eval-rst}
.. autosummary::
   :toctree: api/

   dummy.confused_claim_examiner.ConfusedClaimExaminer
   dummy.fake_claim_extractor.FakeClaimExtractor
   dummy.ignorant_search_engine_retriever.IgnorantSearchEngineRetriever
   dummy.useless_response_regenerator.UselessResponseRegenerator
```

## FactCheckGPT Solvers

```{eval-rst}
.. autosummary::
   :toctree: api/

   factcheckgpt.factcheckgpt_cp.FactCheckGPTClaimProcessor
   factcheckgpt.factcheckgpt_rtv.FactCheckGPTRetriever
   factcheckgpt.factcheckgpt_vfr.FactCheckGPTVerifier
```

## Factool Solvers

```{eval-rst}
.. autosummary::
   :toctree: api/

   factool.all_pass_abstain_detector.AllPassAbstainDetector
   factool.concat_response_regenerator.ConcatResponseRegenerator
   factool.factool_blackbox_post_editor.FactoolBlackboxPostEditor
   factool.factool_blackbox.FactoolBlackboxSolver
   factool.factool_claim_examiner.FactoolClaimExaminer
   factool.factool_decontextualizer.FactoolDecontextualizer
   factool.factool_evidence_retriever.FactoolEvidenceRetriever
   factool.factool_post_editor.FactoolPostEditor
```

## RARR Solvers

```{eval-rst}
.. autosummary::
   :toctree: api/

   rarr.rarr_agreement_gate.RARRAgreementGate
   rarr.rarr_concat_response_regenerator.RARRConcatResponseRegenerator
   rarr.rarr_editor.RARREditor
   rarr.rarr_llm_retriever.RARRLLMRetriever
   rarr.rarr_question_generator.RARRQuestionGenerator
   rarr.rarr_search_engine_retriever.RARRSearchEngineRetriever
```

## Tutorial Solvers

```{eval-rst}
.. autosummary::
   :toctree: api/

   tutorial.all_pass_abstain_detector.AllPassAbstainDetector
   tutorial.chatgpt_decontextulizer.ChatGPTDecontextualizer
   tutorial.chatgpt_post_editor.ChatGPTPostEditor
   tutorial.chatgpt_worthiness_filter.ChatGPTWorthinessFilter
   tutorial.concat_response_regenerator.ConcatResponseRegenerator
   tutorial.search_engine_evidence_retriever.SearchEngineEvidenceRetriever
   tutorial.spacy_response_decomposer.SpacyResponseDecomposer
```

## WebService Solvers

```{eval-rst}
.. autosummary::
   :toctree: api/

   webservice.factcheckgpt_cp.FactCheckGPTClaimProcessor
   webservice.factcheckgpt_rtv.FactCheckGPTRetriever
   webservice.factcheckgpt_vfr.FactCheckGPTVerifier
   webservice.ftool_cp.FactoolClaimProcessor
   webservice.ftool_rtv.FactoolRetriever
   webservice.ftool_vfr.FactoolVerifier
   webservice.rarr_rtv.RARRRetriever
   webservice.rarr_vfr.RARRAgreementGate
```
