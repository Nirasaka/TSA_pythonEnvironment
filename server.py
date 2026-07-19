from flask import Flask, send_file, jsonify
import os

app = Flask(__name__)

fishNum = 1

# 魚の番号を保存
def changeNumberFish():
    global fishNum
    
    fishNum +=1
    if fishNum > 15:
        fishNum = 1
        
def getFish():
    global fishNum
    path = "./output/mesh/me_fish_data("+str(fishNum)+").obj"
    return path
    

@app.route('/download', methods=['GET'])
def download_file():
    fishPath = getFish()
    changeNumberFish()
    print(fishNum)
    print(fishPath)
    if not os.path.exists(fishPath):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(fishPath)

if __name__ == '__main__':
    app.run(debug=True, host='150.89.239.35', port=5000)
