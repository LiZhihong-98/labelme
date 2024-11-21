# from transformers import AutoModelForCausalLM, AutoTokenizer
# import torch


# def generate_response(prompt: str, model_name="Qwen/Qwen2.5-1.5B-Instruct"):
#     """
#     生成基于提示的文本回复
#     :param prompt: 用户输入的提示文本
#     :param model_name: 使用的预训练模型名称，默认使用 "Qwen/Qwen2.5-3B-Instruct"
#     :return: 生成的文本回复
#     """
#     # 加载模型
#     model = AutoModelForCausalLM.from_pretrained(
#         model_name, torch_dtype="auto", device_map="auto"
#     )

#     # 加载tokenizer
#     tokenizer = AutoTokenizer.from_pretrained(model_name)

#     try:
#         # 构建消息列表
#         messages = [
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": prompt},
#         ]

#         # 使用chat模板格式化消息
#         text = tokenizer.apply_chat_template(
#             messages, tokenize=False, add_generation_prompt=True
#         )
#         print(text)

#         # tokenizer编码
#         model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

#         # 生成文本
#         generated_ids = model.generate(**model_inputs, max_new_tokens=100)

#         # 解码生成的文本
#         generated_ids = [
#             output_ids[len(input_ids) :]  # 跳过输入的token部分
#             for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
#         ]

#         # 返回生成的文本
#         response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
#         return response
#     finally:
#         # 显式释放内存
#         del model
#         del tokenizer
#         torch.cuda.empty_cache()  # 如果使用 GPU，清理缓存
