# ============================================================
# Image Caption Generator using CNN + LSTM
# Developed by Deepak Kumar Saini
# ============================================================

import os
import pickle
import numpy as np
import streamlit as st
import tensorflow as tf

from gtts import gTTS

from tensorflow.keras.models import Model, load_model
from tensorflow.keras.applications.vgg16 import (
    VGG16,
    preprocess_input
)
from tensorflow.keras.preprocessing.image import (
    load_img,
    img_to_array
)
from tensorflow.keras.preprocessing.sequence import (
    pad_sequences
)

# ============================================================
# Streamlit Page Configuration
# ============================================================

st.set_page_config(
    page_title="AI Image Caption Generator",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Custom CSS
# ============================================================

st.markdown(
"""
<style>

.main{
    background-color:#f7f9fc;
}

h1{
    text-align:center;
    color:#1565C0;
}

h2,h3{
    color:#0D47A1;
}

.caption-box{
    background:#E3F2FD;
    padding:20px;
    border-radius:10px;
    font-size:22px;
    color:#000;
}

.footer{
    text-align:center;
    color:gray;
    font-size:14px;
}

</style>
""",
unsafe_allow_html=True
)


# ============================================================
# Cache Models
# ============================================================

@st.cache_resource
def load_models():

    # Load VGG16 Feature Extractor
    base_model = VGG16()

    feature_extractor = Model(
        inputs=base_model.inputs,
        outputs=base_model.layers[-2].output
    )

    # Load Caption Model
    caption_model = load_model("model.h5")

    # Load Tokenizer
    with open("tokenizer.pkl", "rb") as f:
        tokenizer = pickle.load(f)

    return feature_extractor, caption_model, tokenizer


feature_extractor, caption_model, tokenizer = load_models()

# ============================================================
# Fast Index -> Word
# ============================================================

index_to_word = tokenizer.index_word


def get_word(index):

    return index_to_word.get(index)

# ============================================================
# Main Title
# ============================================================

st.title("📷 AI Image Caption Generator")

st.markdown("---")

# ============================================================
# Upload Image
# ============================================================

uploaded_image = st.file_uploader(
    "📤 Upload an Image",
    type=["jpg", "jpeg", "png"]
)

# ============================================================
# Caption Prediction
# ============================================================

def predict_caption(
    model,
    image_features,
    tokenizer,
    max_caption_length=35
):

    caption = "startseq"

    for _ in range(max_caption_length):

        sequence = tokenizer.texts_to_sequences(
            [caption]
        )[0]

        sequence = pad_sequences(
            [sequence],
            maxlen=max_caption_length
        )

        prediction = model.predict(
            [image_features, sequence],
            verbose=0
        )

        predicted_index = np.argmax(prediction)

        predicted_word = get_word(predicted_index)

        if predicted_word is None:
            break

        caption += " " + predicted_word

        if predicted_word == "endseq":
            break

    caption = caption.replace("startseq", "")

    caption = caption.replace("endseq", "")

    return caption.strip()


# ============================================================
# Process Uploaded Image
# ============================================================

if uploaded_image is not None:

    col1, col2 = st.columns([1, 1])

    with col1:

        st.subheader("🖼 Uploaded Image")

        st.image(
            uploaded_image,
            use_container_width=True
        )

    with col2:

        st.subheader("⚙ Processing")

        progress = st.progress(0)

        status = st.empty()

        status.write("Loading image...")

        image = load_img(
            uploaded_image,
            target_size=(224,224)
        )

        progress.progress(20)

        image = img_to_array(image)

        image = image.reshape(
            (
                1,
                image.shape[0],
                image.shape[1],
                image.shape[2]
            )
        )

        image = preprocess_input(image)

        status.write("Extracting VGG16 Features...")

        progress.progress(50)

        image_features = feature_extractor.predict(
            image,
            verbose=0
        )

        status.write("Generating Caption...")

        progress.progress(80)

        generated_caption = predict_caption(
            caption_model,
            image_features,
            tokenizer,
            35
        )

        progress.progress(100)

        status.success("Caption Generated Successfully ✅")

        # ============================================================
# Display Results
# ============================================================

        st.markdown("---")

        st.subheader("📝 Generated Caption")

        st.markdown(
            f"""
            <div class="caption-box">
            {generated_caption}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("---")


        # ====================================================
        # Text To Speech
        # ====================================================

        st.subheader("🔊 Listen to Caption")

        if generated_caption.strip() != "":

            tts = gTTS(
                text=generated_caption,
                lang="en"
            )

            audio_file = "caption.mp3"

            tts.save(audio_file)

            st.audio(audio_file)

        st.markdown("---")

        # ====================================================
        # Download Caption
        # ====================================================

        st.download_button(
            label="📥 Download Caption",
            data=generated_caption,
            file_name="generated_caption.txt",
            mime="text/plain"
        )

        st.markdown("---")

        st.success("✅ Caption generation completed successfully!")

else:

    st.info("📤 Upload an image to generate a caption.")

