import streamlit as st
import json
import requests
import time
from PIL import Image
from io import BytesIO
import base64
from fpdf import FPDF

word_count = 100

class AIApp:
    def __init__(self):
        self.API_TOKEN = "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"  # Replace with your actual token
        self.model_urls = {
            "Qwen2.5-Coder-32B-Instruct": "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-32B-Instruct",
            "microsoft/Phi-3.5-mini-instruct": "https://api-inference.huggingface.co/models/microsoft/Phi-3.5-mini-instruct",
            "meta-llama/Llama-3.2-1B": "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-1B",
        }
        self.image_model_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"

    def generate_text(self, prompt, model_url, max_tokens=200, retries=3, wait_time=20):
        headers = {"Authorization": f"Bearer {self.API_TOKEN}"}
        data = {"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}}

        for attempt in range(retries):
            resp = requests.post(model_url, headers=headers, json=data)
            if resp.status_code == 200:
                out = resp.json()
                # some HF models return dict, some list
                if isinstance(out, list):
                    text = out[0].get("generated_text", "")
                else:
                    text = out.get("generated_text", "")
                text = text.strip()
                if text and not text.endswith(('.', '!', '?')):
                    text += '.'
                return text
            elif resp.status_code == 503:
                st.warning(f"Model loading, retrying in {wait_time}s…")
                time.sleep(wait_time)
            else:
                return f"Error: {resp.status_code} – {resp.text}"
        return "Error: Unable to fetch text response."

    def generate_image(self, prompt, retries=3, wait_time=20):
        headers = {"Authorization": f"Bearer {self.API_TOKEN}"}
        data = {"inputs": prompt}

        for attempt in range(retries):
            resp = requests.post(self.image_model_url, headers=headers, json=data)
            if resp.status_code == 200:
                return resp.content
            elif resp.status_code == 503:
                st.warning(f"Image model loading, retrying in {wait_time}s…")
                time.sleep(wait_time)
            else:
                return f"Error: {resp.status_code} – {resp.text}"
        return "Error: Unable to fetch image."

    def create_pdf(self, generated_text, generated_image=None):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Generated Content", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", '', 12)
        if generated_text:
            pdf.multi_cell(0, 10, generated_text)

        if isinstance(generated_image, (bytes, bytearray)):
            image_path = "temp_image.jpg"
            with open(image_path, "wb") as img_file:
                img_file.write(generated_image)
            pdf.ln(10)
            pdf.image(image_path, x=10, y=pdf.get_y(), w=180)
            pdf.ln(80)

        return pdf.output(dest='S').encode('latin1')

    def main(self):
        st.subheader("AI Image and Text Generation Tool")
        generation_type = st.radio(
            "Select Generation Type",
            ["Image Generation", "Text Generation", "Both Text & Image Generation"],
            horizontal=True
        )
        user_prompt = st.text_area("Enter your prompt:", "May lord krishna bless you ")

        if generation_type == "Both Text & Image Generation":
            if st.button("Generate Text & Image"):
                with st.spinner("Generating…"):
                    text = self.generate_text(
                        user_prompt,
                        list(self.model_urls.values())[0],
                        max_tokens=word_count
                    )
                    img_bytes = self.generate_image(user_prompt)

                    if isinstance(img_bytes, (bytes, bytearray)):
                        img = Image.open(BytesIO(img_bytes))
                        st.image(img, caption="Generated Image", use_container_width=True)

                    st.markdown(f"<div class='generated-text'>{text}</div>", unsafe_allow_html=True)
                    pdf_data = self.create_pdf(text, img_bytes)
                    st.download_button("Download PDF", data=pdf_data,
                                       file_name="generated_content.pdf",
                                       mime="application/pdf")

        elif generation_type == "Text Generation":
            st.subheader("Text Generation")
            model_name = st.selectbox("Choose a model", list(self.model_urls.keys()))
            if st.button("Generate Text"):
                with st.spinner("Generating text…"):
                    text = self.generate_text(user_prompt, self.model_urls[model_name], max_tokens=word_count)
                    st.markdown(f"<div class='generated-text'>{text}</div>", unsafe_allow_html=True)
                    pdf_data = self.create_pdf(text)
                    st.download_button("Download PDF", data=pdf_data,
                                       file_name="generated_content.pdf",
                                       mime="application/pdf")

        else:  # Image Generation
            st.subheader("Image Generation")
            if st.button("Generate Image"):
                with st.spinner("Generating image…"):
                    img_bytes = self.generate_image(user_prompt)
                    if isinstance(img_bytes, (bytes, bytearray)):
                        img = Image.open(BytesIO(img_bytes))
                        st.image(img, caption="Generated Image", use_container_width=True)
                    pdf_data = self.create_pdf("", img_bytes)
                    st.download_button("Download PDF", data=pdf_data,
                                       file_name="generated_content.pdf",
                                       mime="application/pdf")


if __name__ == "__main__":
    AIApp().main()
