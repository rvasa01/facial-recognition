import argparse
import os
import sys
import json
#import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np

from inference.FaceRecognizer import FaceRecognizer

# FLAGS
parser = argparse.ArgumentParser(description='Parsing args for generate database')
parser.add_argument("--images", type=str, help="face image path organized by names", required=True)
parser.add_argument("--db_dir", type=str, help="database output directory", default='.')
args = parser.parse_args()


if __name__ == '__main__':

    # model path
    REC_MODEL_PATH_TPU = "../pretrained_model/edgetpu_v2/model_with_mask_clf_quant_edgetpu.tflite"
    recognizer = FaceRecognizer(REC_MODEL_PATH_TPU)

    # buffer
    # label = []
    # db = []
# Load existing database and labels if they exist
    db_path = os.path.join(args.db_dir, "db.npy")
    label_path = os.path.join(args.db_dir, "label.npy")
    input = input("Enter label: ")
     # Initialize or load existing data
    if os.path.exists(db_path) and os.path.exists(label_path):
        print("Loading existing database...")
        existing_db = np.load(db_path)
        existing_labels = np.load(label_path)
        db = existing_db.tolist()
        label = existing_labels.tolist()
        print(f"Loaded {len(label)} existing embeddings")
    else:
        print("Creating new database...")
        db = []
        label = []
    label_json_path = "../pretrained_model/label.json"
    if os.path.exists(label_json_path):
        with open(label_json_path, 'r') as f:
            label_dict = json.load(f)
        # Get the next available index
        next_index = max(map(int, label_dict.keys())) + 1
    else:
        label_dict = {}
        next_index = 0
    for file in os.listdir(args.images):
        try:
            image = plt.imread(os.path.join(args.images, file))
            print("file: ", file)
            embedding, mask = recognizer.face_recognize(image)  # Unpack both returns
            # Ensure embedding is the correct shape (squeeze if needed)
           # embedding = embedding.squeeze()
            embedding = embedding / np.expand_dims(np.sqrt(np.sum(np.power(embedding, 2), 1)), 1)
            #print("embedding: ", embedding)
            # if embedding.ndim != 1:  # Check if embedding is 1D
            #     print(f"Skipping {file}: Invalid embedding shape {embedding.shape}")
            #     continue
            label_dict[str(next_index)] = input
            next_index += 1
            label.append(file.split('.')[0])
            db.append(embedding)
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
            continue
    with open(label_json_path, 'w') as f:
        json.dump(label_dict, f, indent=2)
    print(f"Updated label.json with {next_index} entries")
    # write to file
    if len(label) > 0:
        try:
            # Convert to numpy array and ensure consistent shape
            db_array = np.array(db)
            print(f"Database shape: {db_array.shape}")  # Debug info
            
            # Save files
            np.save(os.path.join(args.db_dir, "label"), np.array(label))
            np.save(os.path.join(args.db_dir, "db"), db_array)
            print(f"Saved {len(label)} embeddings with shape {db_array.shape}")
        except Exception as e:
            print(f"Error saving database: {str(e)}")
