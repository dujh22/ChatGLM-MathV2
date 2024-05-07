@echo off

SET project_path=F://code//github//ChatGLM-MathV2//
cd %project_path%

echo Starting the data preprocessing pipeline...

cd %project_path%utils
SET input_file_path=%project_path%raw_data//peiyi9979_Math_Shepherd//math-shepherd.jsonl
SET num_points=10
SET new_folder_suffix=math_shepherd_test_data%num_points%
SET language=en
SET output_file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%.jsonl
python data_preprocessing.py %input_file_path% %output_file_path% %num_points% %language%

echo Data preprocessing completed.

echo Starting backend generation...

cd %project_path%shepherd_prm
SET prompt_template_path=%project_path%shepherd_prm//templates//criticllm_math_template.txt
SET prompt_key=question
SET response_key=response
SET reference_key=solution

SET backbone=tgi
SET input_file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%.jsonl
SET mode=response
SET num_process=10

python query_api.py --input_file %input_file_path% --prompt_template %prompt_template_path% --prompt_key %prompt_key% --response_key %response_key% --reference_key %reference_key% --backbone %backbone% --mode %mode% --num_process %num_process%

echo Backend generation completed.
echo Starting backend scoring...

SET backbone=chatglm_platform
SET input_file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%_tgi.jsonl
SET mode=critic
SET num_process=10

python query_api.py --input_file %input_file_path% --prompt_template %prompt_template_path% --prompt_key %prompt_key% --response_key %response_key% --reference_key %reference_key% --backbone %backbone% --mode %mode% --num_process %num_process%

echo Backend scoring completed.
echo Starting forward process path prediction...

SET prompt_template_path=%project_path%shepherd_prm//templates//criticllm_math_template.txt
SET prompt_key=question
SET response_key=response
SET reference_key=solution
SET process_response_key=generated_paths
SET reference_answewr_key=solution

SET backbone=tgi
SET input_file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%_tgi_math_critic.jsonl
SET mode=generation
SET num_process=10

python prm_evaluate_process.py --input_file %input_file_path% --prompt_template %prompt_template_path% --prompt_key %prompt_key% --response_key %response_key% --reference_key %reference_key% --process_response_key %process_response_key% --reference_answer_key %reference_answer_key% --backbone %backbone% --mode %mode% --num_process %num_process%

echo Forward process path prediction completed.
echo Starting forward process path evaluation...

SET backbone=chatglm_platform
SET input_file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%_tgi_math_critic_path.jsonl
SET mode=critic

python prm_evaluate_process.py --input_file %input_file_path% --prompt_template %prompt_template_path% --prompt_key %prompt_key% --response_key %response_key% --reference_key %reference_key% --process_response_key %process_response_key% --reference_answer_key %reference_answer_key% --backbone %backbone% --mode %mode% --num_process %num_process%

echo Forward process path evaluation completed.
echo Calculating accuracy...

SET file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%_tgi_math_critic_path_math_critic2.jsonl
SET output_file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%_tgi_math_critic_path_math_critic2_statistics.csv

python Check3_CalculatePathPredictAccuracy.py %file_path% %output_file_path%

echo Accuracy calculation completed.
echo Starting forward automatic labeling...

cd %project_path%utils

SET input_file_path=%project_path%data//%new_folder_suffix%//%new_folder_suffix%_tgi.jsonl
SET output_file_path=%project_path%data//%new_folder_suffix%//front//%new_folder_suffix%.jsonl
python turn_response_and_solution.py %input_file_path% %output_file_path%

cd %project_path%

SET source_folder=%project_path%data//%new_folder_suffix%//front
SET target_folder=%project_path%data//%new_folder_suffix%//front_step1
python Step1_SplitByRow.py %source_folder% %target_folder%

echo Forward automatic labeling finished Step1_SplitByRow.

SET source_folder=%project_path%data//%new_folder_suffix%//front_step1
SET target_folder=%project_path%data//%new_folder_suffix%//front_step2
python Step2_IsCalculationOrReasoning.py %source_folder% %target_folder%

echo Forward automatic labeling finished Step2_IsCalculationOrReasoning.

SET source_folder=%project_path%data//%new_folder_suffix%//front_step2
SET target_folder=%project_path%data//%new_folder_suffix%//front_step3
python Step3_JudgmentStepCalculatedCorrectly.py %source_folder% %target_folder%

echo Forward automatic labeling finished Step3_JudgmentStepCalculatedCorrectly.

SET source_folder=%project_path%data//%new_folder_suffix%//front_step3
SET target_folder=%project_path%data//%new_folder_suffix%//front_step4
python Step4_JudgmentStepReasoningCorrectly.py %source_folder% %target_folder%

echo Forward automatic labeling finished Step4_JudgmentStepReasoningCorrectly.

echo Forward automatic labeling completed.
echo All steps completed successfully!

pause
