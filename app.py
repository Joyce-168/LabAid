# 前端頁面
import gradio as gr
from utils import generate_answer # 從 utils 導入

# Global buttons
start_chatbot_btn = gr.Button("Start Chatbot", visible=True)

def show_chatbot_page():
    return gr.update(visible=False), gr.update(visible=True)

def show_main_ui_page():
    # 清空聊天歷史，確保返回主頁時聊天框是空的
    return gr.update(visible=True), gr.update(visible=False), None 


with gr.Blocks(css="styles.css", title="LabAid AI") as demo: # 引用外部 CSS 文件
    main_ui_section = gr.Column(visible=True)
    chatbot_section = gr.Column(visible=False, elem_id="chatbot-section")

    with main_ui_section:
        gr.HTML("""
         <div style="display: flex; justify-content: space-between; align-items: center; padding: 20px; background-color: white; border-bottom: 1px solid #f0f0f0;">
             <div style="font-size: 1.5em; font-weight: bold; color: #1a2b4b;">LabAid AI</div>
             <div>
                <a href="#" style="margin-left: 25px; color: #4a5b7d; text-decoration: none;">Features</a>
                <a href="#" style="margin-left: 25px; color: #4a5b7d; text-decoration: none;">How It Works</a>
             </div>
         </div>
        """)

    # --- AI-Powered Lab Troubleshooting 主區塊 ---
        with gr.Column(elem_id="hero-section", scale=1):
            gr.Markdown(
            """
            <h1 style="text-align: center; font-size: 3.5em; margin-top: 50px; margin-bottom: 20px;">AI-Powered Lab Troubleshooting</h1>
            <p style="text-align: center; font-size: 1.2em; max-width: 800px; margin: 0 auto 40px auto; line-height: 1.6;">Instantly diagnose and resolve equipment issues with our intelligent AI assistant. Get step-by-step solutions, maintenance tips, and expert guidance 24/7.</p>
            """,
            label="")
            gr.Row(scale=1)
            start_chatbot_btn.render()

    # --- How It Works 三步流程 ---
        gr.Markdown("""
        <h2 style="text-align: center; margin-top: 80px; margin-bottom: 20px;">How It Works</h2>
        <p style="text-align: center; font-size: 1.1em; max-width: 600px; margin: 0 auto 60px auto;">Get your equipment back online in three simple steps</p>
        """,
        label="")
        with gr.Column(elem_classes="card-container"):
            with gr.Row(elem_id="how-it-works-section"):
               with gr.Column(scale=1):
                   gr.HTML('<div class="circle-number">1</div>')
                   gr.Markdown( """
                <h3 style="text-align: center;">Describe the Issue</h3>
                <p style="text-align: center;">Simply tell our AI what's wrong with your equipment. Use natural language - no technical jargon required.</p>
                """)
               with gr.Column(scale=1):
                  gr.HTML('<div class="circle-number">2</div>')
                  gr.Markdown("""
                <h3 style="text-align: center;">Get AI Analysis</h3>
                <p style="text-align: center;">Our advanced AI analyzes your description and equipment type to provide accurate diagnosis and solutions.</p>
                """)
               with gr.Column(scale=1):
                  gr.HTML('<div class="circle-number">3</div>')
                  gr.Markdown("""
                <h3 style="text-align: center;">Follow the Steps</h3>
                <p style="text-align: center;">Receive detailed, step-by-step instructions with visual aids to resolve the issue quickly and safely.</p>
                """)


    # --- Download Resources 區塊 ---
        gr.Markdown("""
        <h2 style="text-align: center; margin-top: 80px; margin-bottom: 20px;">Download Resources</h2>
        <p style="text-align: center; font-size: 1.1em; max-width: 600px; margin: 0 auto 40px auto;">Access comprehensive guides, manuals, and troubleshooting documentation for your lab equipment.</p>
        """,
        label="")

        with gr.Row(elem_id="download-resources-section"):
            with gr.Column(scale=1):
               with gr.Column(elem_classes="card-container"):
                   gr.Markdown("<h4>📄 Equipment Manual</h4><p>Complete user manual for lab equipment operation and safety guidelines.</p><p style='font-size:0.9em; color:#888;'>PDF • 2.4 MB</p>")
                   gr.Button("Download", link="https://example.com/manual.pdf") # 連結到虛擬的下載文件
            with gr.Column(scale=1):
                with gr.Column(elem_classes="card-container"):
                   gr.Markdown("<h4>🔧 Troubleshooting Guide</h4><p>Step-by-step solutions for common equipment issues and error codes.</p><p style='font-size:0.9em; color:#888;'>PDF • 1.8 MB</p>")
                   gr.Button("Download", link="https://example.com/troubleshooting.pdf")
            with gr.Column(scale=1):
                with gr.Column(elem_classes="card-container"):
                   gr.Markdown("<h4>🗓️ Maintenance Schedule</h4><p>Recommended maintenance timeline and procedures for optimal performance.</p><p style='font-size:0.9em; color:#888;'>PDF • 0.9 MB</p>")
                   gr.Button("Download", link="https://example.com/maintenance.pdf")

        gr.Row(scale=1)
        gr.Markdown("""
            <a href="#" style="display: block; text-align: center; margin-top: 30px; font-size: 1.1em; color: #3b82f6; text-decoration: none;">View All Documents &rarr;</a>
            """,
            label="")
    # --- 頁腳 (非常簡化，僅文本模擬) ---
        gr.HTML("""
           <div class="footer">
               <div style="display: flex; justify-content: center; flex-wrap: wrap; margin-bottom: 20px;">
                   <div style="flex-basis: 200px; margin: 0 20px;">
                       <h4 style="color: white; margin-bottom: 10px;">Product</h4>
                       <a href="#">Features</a><br>
                       <a href="#">API</a><br>
                       <a href="#">Documentation</a>
                   </div>
                   <div style="flex-basis: 200px; margin: 0 20px;">
                       <h4 style="color: white; margin-bottom: 10px;">Support</h4>
                       <a href="#">Help Center</a><br>
                       <a href="#">Contact Us</a><br>
                       <a href="#">Status</a><br>
                       <a href="#">Community</a>
                    </div>
                   <div style="flex-basis: 200px; margin: 0 20px;">
                       <h4 style="color: white; margin-bottom: 10px;">Company</h4>
                       <a href="#">About</a><br>
                       <a href="#">Blog</a><br>
                       <a href="#">Careers</a><br>
                       <a href="#">Press</a>
                   </div>
               </div>
               <p style="margin-top: 30px;">&copy; 2024 LabAid AI. All rights reserved.</p>
               <p><a href="#">Privacy Policy</a> | <a href="#">Terms of Service</a></p>
           </div> """)


    with chatbot_section:
        # 修改 respond 函數以符合 Gradio 聊天機器人的新格式
        def respond(message, chat_history):
            # chat_history 傳入時已經是 [{role: ..., content: ...}, ...] 格式
            # generate_answer 函數會處理這個格式，並返回純文本響應
            ai_response = generate_answer(message, chat_history)
            
            # 將新的用戶消息和 AI 響應添加到歷史記錄中
            # 注意：這裡的 chatbot 已經是 gr.Chatbot(type="messages")
            # 所以傳入的 chat_history 已經是字典列表
            # 我們只需要直接 append 新的 message 和 ai_response 即可
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": ai_response})

            return chat_history

        with gr.Column(elem_id="chatbot-header"):
            gr.Markdown("## AI Chatbot for Lab Troubleshooting")
            back_to_main_btn = gr.Button("\u2190 Back to Main Page", size="lg")

        chatbot = gr.Chatbot(
            label="Agent",
            # 將 type 設定為 "messages" 以使用新的數據格式
            type="messages", 
            avatar_images=(
                None, # 用戶頭像 (可以留空)
                "https://em-content.zobj.net/source/twitter/376/hugging-face_1f917.png", # AI 頭像
            ),
            height=500
        )

        prompt = gr.Textbox(max_lines=1, label="Chat Message", placeholder="Ask me about your lab equipment issues...")

        prompt.submit(
            fn=respond,
            inputs=[prompt, chatbot],
            outputs=[chatbot],
        ).then(
            lambda: "", None, prompt
        )

    # Button actions
    start_chatbot_btn.click(
        fn=show_chatbot_page,
        inputs=[],
        outputs=[main_ui_section, chatbot_section]
    )

    back_to_main_btn.click(
        fn=show_main_ui_page,
        inputs=[],
        outputs=[main_ui_section, chatbot_section, chatbot] # 返回主頁時清空聊天框
    )

if __name__ == "__main__":
    demo.launch()