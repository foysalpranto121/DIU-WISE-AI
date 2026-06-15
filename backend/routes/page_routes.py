from flask import Blueprint, render_template, current_app, jsonify, request
from flask_login import login_required, current_user
import random
import json
import os
from models import db, Appointment

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/mood-history')
@login_required
def mood_history():
    # Mock mood history data for visualization
    mood_data = [
        {"day": "Mon", "mood": 4, "stress": 3},
        {"day": "Tue", "mood": 3, "stress": 5},
        {"day": "Wed", "mood": 5, "stress": 2},
        {"day": "Thu", "mood": 2, "stress": 7},
        {"day": "Fri", "mood": 4, "stress": 4},
        {"day": "Sat", "mood": 5, "stress": 1},
        {"day": "Sun", "mood": 5, "stress": 2},
    ]
    return render_template('mood_history.html', mood_data=mood_data)

@pages_bp.route('/resources')
@login_required
def resources():
    # --- DOCUMENTS ---
    documents = [
        {
            "id": "doc-1",
            "title": "Managing Midterm Stress",
            "category": "Mental Health",
            "type": "Document",
            "icon": "📄",
            "summary": "Proven techniques to stay calm and focused during high-pressure exam weeks. Includes breathing exercises, time-boxing, and CBT strategies.",
            "author": "Dr. Sarah Chen",
            "read_time": "8 min read",
            "date": "2025-03-15",
            "featured": True,
            "content": """<h2>Understanding Midterm Stress</h2>
<p>Midterm exams are one of the most stressful periods for university students. Research from the American Psychological Association shows that 61% of college students report anxiety as their top mental health concern, with exam periods amplifying stress levels significantly.</p>

<h3>1. The 4-7-8 Breathing Technique</h3>
<p>This evidence-based technique activates your parasympathetic nervous system:</p>
<ul>
<li><strong>Inhale</strong> through your nose for 4 seconds</li>
<li><strong>Hold</strong> your breath for 7 seconds</li>
<li><strong>Exhale</strong> slowly through your mouth for 8 seconds</li>
<li>Repeat 3-4 cycles before each study session</li>
</ul>

<h3>2. Time-Boxing Your Study Sessions</h3>
<p>Break study time into focused 25-minute blocks (Pomodoro Technique) followed by 5-minute breaks. After 4 blocks, take a longer 15-30 minute break. This prevents burnout and maintains cognitive performance.</p>

<h3>3. Cognitive Behavioral Strategies</h3>
<p>Challenge negative thoughts by asking:</p>
<ul>
<li>"Is this thought based on facts or feelings?"</li>
<li>"What would I tell a friend in this situation?"</li>
<li>"What's the most realistic outcome?"</li>
</ul>

<h3>4. Physical Well-being During Exams</h3>
<p>Don't sacrifice sleep for study time. Research consistently shows that students who sleep 7-8 hours perform better on exams than those who pull all-nighters. Maintain regular meals and stay hydrated.</p>

<blockquote>"The greatest weapon against stress is our ability to choose one thought over another." — William James</blockquote>"""
        },
        {
            "id": "doc-2",
            "title": "The Pomodoro Technique for Students",
            "category": "Productivity",
            "type": "Document",
            "icon": "📄",
            "summary": "A complete guide to structuring your study sessions for maximum focus, retention, and productivity using time management science.",
            "author": "Prof. Mark Williams",
            "read_time": "12 min read",
            "date": "2025-02-20",
            "featured": False,
            "content": """<h2>Master Your Time with Pomodoro</h2>
<p>The Pomodoro Technique, developed by Francesco Cirillo, is one of the most effective time management methods for students. It leverages the science of focused attention and strategic breaks.</p>

<h3>How It Works</h3>
<ol>
<li><strong>Choose a task</strong> — Pick one subject or assignment to focus on</li>
<li><strong>Set a timer for 25 minutes</strong> — This is one "Pomodoro"</li>
<li><strong>Work with full focus</strong> — No phone, no social media, no distractions</li>
<li><strong>Take a 5-minute break</strong> — Stand up, stretch, hydrate</li>
<li><strong>After 4 Pomodoros</strong> — Take a 15-30 minute break</li>
</ol>

<h3>Why It Works</h3>
<p>Research in cognitive psychology shows that our attention span naturally fluctuates. By working in short, intense bursts, you align with your brain's natural rhythm. The breaks prevent mental fatigue and allow for memory consolidation.</p>

<h3>Tips for DIU Students</h3>
<ul>
<li>Use the technique during library study sessions</li>
<li>Track your daily Pomodoro count to build consistency</li>
<li>Pair it with active recall and spaced repetition for maximum retention</li>
</ul>"""
        },
        {
            "id": "doc-3",
            "title": "Better Sleep, Better Grades",
            "category": "Wellness",
            "type": "Document",
            "icon": "📄",
            "summary": "Exploring the scientific link between sleep quality and academic performance, with actionable tips for building a healthy sleep routine.",
            "author": "Dr. Ayesha Rahman",
            "read_time": "10 min read",
            "date": "2025-04-01",
            "featured": False,
            "content": """<h2>The Sleep-Performance Connection</h2>
<p>A Harvard Medical School study found that students who consistently got 7-9 hours of sleep scored an average of 25% higher on exams compared to sleep-deprived peers.</p>

<h3>Sleep Hygiene Essentials</h3>
<ul>
<li><strong>Consistent schedule:</strong> Go to bed and wake up at the same time daily</li>
<li><strong>Digital sunset:</strong> No screens 1 hour before bed</li>
<li><strong>Cool environment:</strong> Keep your room between 65-68°F (18-20°C)</li>
<li><strong>Caffeine cutoff:</strong> No caffeine after 2 PM</li>
<li><strong>Wind-down routine:</strong> Read, meditate, or journal before sleep</li>
</ul>

<h3>The Impact on Memory</h3>
<p>During deep sleep, your brain consolidates memories from the day. This means that studying before bed and getting quality sleep is one of the most effective learning strategies available.</p>"""
        },
        {
            "id": "doc-4",
            "title": "DIU Counseling Services Guide",
            "category": "Campus Support",
            "type": "Document",
            "icon": "📄",
            "summary": "Complete guide to accessing free, confidential counseling services available to all DIU students. Includes booking info and what to expect.",
            "author": "DIU Wellness Team",
            "read_time": "5 min read",
            "date": "2025-01-10",
            "featured": False,
            "content": """<h2>Your Mental Health Matters</h2>
<p>Daffodil International University provides free, confidential counseling services to all enrolled students. Whether you're dealing with academic stress, personal issues, or just need someone to talk to, professional help is available.</p>

<h3>How to Book a Session</h3>
<ol>
<li>Visit the Student Wellness Center (Building 4, 3rd Floor)</li>
<li>Call the helpline: +880-2-XXXXXXX</li>
<li>Email: counseling@daffodilvarsity.edu.bd</li>
<li>Book online through the DIU Student Portal</li>
</ol>

<h3>What to Expect</h3>
<p>Sessions are 45-60 minutes long, completely confidential, and conducted by licensed counselors. You can discuss anything from exam anxiety to relationship issues to career confusion. There's absolutely no stigma — seeking help is a sign of strength.</p>

<h3>Emergency Support</h3>
<p>If you or someone you know is in crisis, contact the 24/7 emergency helpline immediately. You are not alone.</p>"""
        },
        {
            "id": "doc-5",
            "title": "Building Emotional Resilience",
            "category": "Mental Health",
            "type": "Document",
            "icon": "📄",
            "summary": "Learn how to develop emotional resilience to navigate university challenges, setbacks, and pressure with confidence and grace.",
            "author": "Dr. Faisal Hossain",
            "read_time": "15 min read",
            "date": "2025-05-01",
            "featured": True,
            "content": """<h2>What Is Emotional Resilience?</h2>
<p>Emotional resilience is your ability to adapt to stressful situations and bounce back from adversity. It doesn't mean you won't experience difficulty — it means you'll recover faster and grow stronger from challenges.</p>

<h3>The Five Pillars of Resilience</h3>
<ol>
<li><strong>Self-Awareness:</strong> Understand your emotions without judgment</li>
<li><strong>Mindfulness:</strong> Stay present instead of catastrophizing the future</li>
<li><strong>Connection:</strong> Build and maintain supportive relationships</li>
<li><strong>Purpose:</strong> Connect your daily actions to your larger goals</li>
<li><strong>Adaptability:</strong> Embrace change as an opportunity for growth</li>
</ol>

<h3>Daily Resilience Practices</h3>
<ul>
<li>Start each morning with 3 things you're grateful for</li>
<li>Journal for 5 minutes about your feelings</li>
<li>Practice one act of kindness daily</li>
<li>End each day by acknowledging one thing you handled well</li>
</ul>

<blockquote>"The oak fought the wind and was broken, the willow bent when it must and survived." — Robert Jordan</blockquote>"""
        },
    ]

    # --- MOTIVATIONAL STORIES ---
    stories = [
        {
            "id": "story-1",
            "title": "From Failure to Fortune: Jack Ma's Journey",
            "category": "Inspiration",
            "type": "Story",
            "icon": "📖",
            "summary": "Rejected from 30 jobs including KFC, Jack Ma went on to build Alibaba into a $200B empire. A story of relentless perseverance.",
            "author": "DIU Motivation Team",
            "read_time": "6 min read",
            "date": "2025-03-01",
            "featured": True,
            "content": """<h2>The Man Who Never Gave Up</h2>
<p>Jack Ma failed his college entrance exam twice. He was rejected from 30 jobs — including KFC, which hired 23 out of 24 applicants. Harvard rejected him 10 times. Yet he went on to create Alibaba, one of the world's largest e-commerce companies.</p>

<h3>Key Lessons</h3>
<ul>
<li><strong>"Today is hard, tomorrow will be worse, but the day after tomorrow will be sunshine."</strong> — Jack Ma didn't expect instant success. He prepared for the long game.</li>
<li><strong>Rejection is redirection.</strong> Every "no" pushed him closer to his true calling.</li>
<li><strong>Start before you're ready.</strong> When Ma started Alibaba in his apartment in 1999, he had no technical background and limited funds.</li>
</ul>

<h3>How This Applies to You</h3>
<p>As a DIU student, you will face rejection — failed exams, missed opportunities, tough feedback. But remember: every successful person has a story of failure. Your current struggle is part of your future success story.</p>

<blockquote>"If you don't give up, you still have a chance. Giving up is the greatest failure." — Jack Ma</blockquote>"""
        },
        {
            "id": "story-2",
            "title": "The Bamboo Tree: A Lesson in Patience",
            "category": "Inspiration",
            "type": "Story",
            "icon": "📖",
            "summary": "The Chinese bamboo tree teaches us that growth often happens invisibly before the breakthrough moment. Keep nurturing your dreams.",
            "author": "DIU Motivation Team",
            "read_time": "4 min read",
            "date": "2025-02-14",
            "featured": False,
            "content": """<h2>The Bamboo Tree Parable</h2>
<p>A farmer plants a Chinese bamboo seed. He waters it and waits. After the first year — nothing. Second year — nothing. Third year — still nothing. Fourth year — nothing visible above the ground.</p>
<p>But in the fifth year, the bamboo tree grows <strong>80 feet in just six weeks</strong>.</p>

<h3>What Was Happening Underground?</h3>
<p>For four years, the bamboo was building an extensive root system deep underground — a foundation strong enough to support its explosive growth. Without those invisible years of preparation, the tree could never have grown so tall.</p>

<h3>Your University Years Are Your Root System</h3>
<p>Right now, you might feel like nothing is happening. You study hard but results seem slow. You work on projects but recognition doesn't come. But you are building your root system — knowledge, skills, character, connections — that will support your breakthrough moment.</p>

<blockquote>"Don't judge each day by the harvest you reap but by the seeds that you plant." — Robert Louis Stevenson</blockquote>"""
        },
        {
            "id": "story-3",
            "title": "A DIU Student Who Changed Everything",
            "category": "Campus Life",
            "type": "Story",
            "icon": "📖",
            "summary": "How a struggling first-year student transformed their academic journey through mentorship, discipline, and the courage to ask for help.",
            "author": "Anonymous (Shared with permission)",
            "read_time": "7 min read",
            "date": "2025-04-10",
            "featured": True,
            "content": """<h2>My First Semester Was a Disaster</h2>
<p>I came to DIU full of hope but completely unprepared. By mid-semester, I was failing two courses, had no friends, and seriously considered dropping out. I felt like I didn't belong.</p>

<h3>The Turning Point</h3>
<p>One day, after failing a midterm, I sat in the library staring at my results. A senior student noticed me and asked if I was okay. That simple act of kindness changed my life. He became my mentor, helped me create a study schedule, and introduced me to a study group.</p>

<h3>What I Learned</h3>
<ul>
<li><strong>Asking for help isn't weakness — it's wisdom.</strong> I visited the counseling center and it transformed my mindset.</li>
<li><strong>Consistency beats intensity.</strong> I stopped cramming and started studying 2 hours daily.</li>
<li><strong>Community is everything.</strong> My study group became my support system through every challenge.</li>
</ul>

<p>By my final year, I graduated with honors and received a job offer before convocation. If I had given up in that first semester, none of this would have happened.</p>

<blockquote>"The moment you're ready to quit is usually the moment right before a miracle happens."</blockquote>"""
        },
        {
            "id": "story-4",
            "title": "Malala: Education Against All Odds",
            "category": "Inspiration",
            "type": "Story",
            "icon": "📖",
            "summary": "Malala Yousafzai survived an assassination attempt and became the youngest Nobel Prize laureate, fighting for every child's right to education.",
            "author": "DIU Motivation Team",
            "read_time": "5 min read",
            "date": "2025-01-20",
            "featured": False,
            "content": """<h2>One Girl Changed the World</h2>
<p>At age 11, Malala Yousafzai began blogging anonymously about life under Taliban rule in Pakistan's Swat Valley, where girls were banned from attending school. At 15, she was shot in the head by a Taliban gunman on her school bus.</p>

<h3>She Didn't Stop</h3>
<p>After surviving and recovering, Malala became an even more powerful advocate for education. At 17, she became the youngest person ever to receive the Nobel Peace Prize. Her foundation has invested in education programs in over 15 countries.</p>

<h3>Her Message to Students</h3>
<blockquote>"One child, one teacher, one book, one pen can change the world."</blockquote>

<p>Every time you sit in a classroom, open a textbook, or log into a lecture, you are exercising a privilege that millions fight for. Make it count.</p>"""
        },
    ]

    # --- MOTIVATIONAL VIDEOS ---
    videos = [
        {
            "id": "vid-1",
            "title": "The Power of Believing in Yourself",
            "category": "Motivation",
            "type": "Video",
            "icon": "🎬",
            "summary": "A powerful compilation about self-belief, overcoming doubt, and pushing through when the world says you can't.",
            "author": "Motivational Channel",
            "duration": "10:23",
            "date": "2025-03-20",
            "featured": True,
            "youtube_id": "g-jwWYX7Jlo",
            "thumbnail": "https://img.youtube.com/vi/g-jwWYX7Jlo/maxresdefault.jpg"
        },
        {
            "id": "vid-2",
            "title": "Steve Jobs: Stay Hungry, Stay Foolish",
            "category": "Inspiration",
            "type": "Video",
            "icon": "🎬",
            "summary": "Steve Jobs' legendary Stanford commencement speech — connecting the dots, love and loss, and facing death to find purpose.",
            "author": "Stanford University",
            "duration": "15:04",
            "date": "2025-01-15",
            "featured": True,
            "youtube_id": "UF8uR6Z6KLc",
            "thumbnail": "https://img.youtube.com/vi/UF8uR6Z6KLc/maxresdefault.jpg"
        },
        {
            "id": "vid-3",
            "title": "How to Stop Procrastinating",
            "category": "Productivity",
            "type": "Video",
            "icon": "🎬",
            "summary": "Science-backed strategies to beat procrastination and build momentum in your academic and personal life.",
            "author": "Ali Abdaal",
            "duration": "12:45",
            "date": "2025-02-28",
            "featured": False,
            "youtube_id": "DMw8G3RPWrQ",
            "thumbnail": "https://img.youtube.com/vi/DMw8G3RPWrQ/maxresdefault.jpg"
        },
        {
            "id": "vid-4",
            "title": "You Will Never Be Lazy Again",
            "category": "Motivation",
            "type": "Video",
            "icon": "🎬",
            "summary": "A life-changing motivational speech about discipline, purpose, and taking action even when you don't feel like it.",
            "author": "Motiversity",
            "duration": "8:30",
            "date": "2025-04-05",
            "featured": False,
            "youtube_id": "65x2bkAEo2I",
            "thumbnail": "https://img.youtube.com/vi/65x2bkAEo2I/maxresdefault.jpg"
        },
        {
            "id": "vid-5",
            "title": "The Science of Well-Being",
            "category": "Wellness",
            "type": "Video",
            "icon": "🎬",
            "summary": "Yale's most popular course — understanding what truly makes us happy and how to build lasting well-being habits.",
            "author": "Yale University",
            "duration": "18:20",
            "date": "2025-05-10",
            "featured": False,
            "youtube_id": "ZizdB0TgAVM",
            "thumbnail": "https://img.youtube.com/vi/ZizdB0TgAVM/maxresdefault.jpg"
        },
    ]

    # --- SPEECHES ---
    speeches = [
        {
            "id": "speech-1",
            "title": "Denzel Washington: Fall Forward",
            "category": "Motivation",
            "type": "Speech",
            "icon": "🎤",
            "summary": "Denzel Washington's powerful commencement speech about taking risks, failing forward, and never being afraid to fall.",
            "author": "Denzel Washington",
            "duration": "5:42",
            "date": "2025-03-12",
            "featured": True,
            "youtube_id": "tbnzAVRZ9Xc",
            "thumbnail": "https://img.youtube.com/vi/tbnzAVRZ9Xc/maxresdefault.jpg",
            "transcript_excerpt": """
<blockquote>"Every failed experiment is one step closer to success. You've got to take risks. I'll say it again: fall forward."</blockquote>
<p>In this electrifying speech at the University of Pennsylvania, Denzel Washington shares three essential principles:</p>
<ul>
<li><strong>Put God first</strong> — whatever your faith, start with gratitude</li>
<li><strong>Fail big</strong> — don't be afraid to think big and fail spectacularly</li>
<li><strong>Fall forward</strong> — if you're going to fail, fail toward your goals, not away from them</li>
</ul>
<p>"Do you have the guts to fail? If you don't fail, you're not even trying."</p>"""
        },
        {
            "id": "speech-2",
            "title": "Admiral McRaven: Make Your Bed",
            "category": "Discipline",
            "type": "Speech",
            "icon": "🎤",
            "summary": "Navy SEAL Admiral McRaven's famous speech on how small daily habits create ripples of success that change the world.",
            "author": "Admiral William H. McRaven",
            "duration": "19:26",
            "date": "2025-02-01",
            "featured": True,
            "youtube_id": "pxBQLFLei70",
            "thumbnail": "https://img.youtube.com/vi/pxBQLFLei70/maxresdefault.jpg",
            "transcript_excerpt": """
<blockquote>"If you want to change the world, start by making your bed."</blockquote>
<p>Admiral McRaven's speech at UT Austin is one of the most viewed commencement speeches ever. His 10 life lessons from Navy SEAL training include:</p>
<ul>
<li><strong>Start with the small things.</strong> Making your bed gives you your first accomplishment of the day.</li>
<li><strong>Find someone to paddle with.</strong> You can't change the world alone — find your team.</li>
<li><strong>Measure people by the size of their heart.</strong> It's not about physical size or background.</li>
<li><strong>Get over being a sugar cookie.</strong> Sometimes life isn't fair — keep moving.</li>
<li><strong>Don't be afraid of the circuses.</strong> Failures make you stronger.</li>
</ul>"""
        },
        {
            "id": "speech-3",
            "title": "J.K. Rowling: The Fringe Benefits of Failure",
            "category": "Inspiration",
            "type": "Speech",
            "icon": "🎤",
            "summary": "The Harry Potter author speaks about how her greatest failures — divorce, poverty, depression — became the foundation of her success.",
            "author": "J.K. Rowling",
            "duration": "21:07",
            "date": "2025-01-25",
            "featured": False,
            "youtube_id": "wHGqp8lz36c",
            "thumbnail": "https://img.youtube.com/vi/wHGqp8lz36c/maxresdefault.jpg",
            "transcript_excerpt": """
<blockquote>"It is impossible to live without failing at something, unless you live so cautiously that you might as well not have lived at all — in which case, you fail by default."</blockquote>
<p>At Harvard's 2008 commencement, Rowling delivered a masterclass on the value of failure and imagination:</p>
<ul>
<li><strong>Failure stripped away the inessential.</strong> She stopped pretending to be anything other than what she was — a writer.</li>
<li><strong>Rock bottom became a solid foundation.</strong> With nothing left to lose, she was free to build.</li>
<li><strong>Imagination is not just for fantasy.</strong> It's the power to empathize with others whose experiences differ from our own.</li>
</ul>"""
        },
        {
            "id": "speech-4",
            "title": "Muniba Mazari: Iron Lady of Pakistan",
            "category": "Resilience",
            "type": "Speech",
            "icon": "🎤",
            "summary": "Paralyzed at 21 in a car accident, Muniba became an artist, motivational speaker, and UN Women ambassador. A story of unbreakable spirit.",
            "author": "Muniba Mazari",
            "duration": "14:30",
            "date": "2025-04-18",
            "featured": False,
            "youtube_id": "bFQ5YDSEPgs",
            "thumbnail": "https://img.youtube.com/vi/bFQ5YDSEPgs/maxresdefault.jpg",
            "transcript_excerpt": """
<blockquote>"They said I would never be able to walk again, paint, or have a normal life. I chose to prove them wrong."</blockquote>
<p>Muniba Mazari's story is a testament to the human spirit:</p>
<ul>
<li><strong>She turned her wheelchair into a throne.</strong> Instead of seeing limitation, she found freedom.</li>
<li><strong>She painted with broken hands.</strong> Her art became her therapy and her voice.</li>
<li><strong>She chose gratitude over grief.</strong> Every day is a gift, not a guarantee.</li>
</ul>
<p>"When you accept yourself, the whole world accepts you."</p>"""
        },
    ]

    # Combine all resources
    all_resources = documents + stories + videos + speeches

    # Category counts
    categories = {}
    for r in all_resources:
        cat = r["category"]
        categories[cat] = categories.get(cat, 0) + 1

    return render_template(
        'resources.html',
        documents=documents,
        stories=stories,
        videos=videos,
        speeches=speeches,
        all_resources=all_resources,
        categories=categories,
        total_count=len(all_resources)
    )

@pages_bp.route('/privacy-settings')
@login_required
def privacy_settings():
    return render_template('privacy_settings.html')


@pages_bp.route('/counselors')
@login_required
def counselors():
    # Load counselors json database
    json_path = os.path.join(current_app.config['BASE_DIR'], 'data', 'counselors.json')
    counselors_list = []
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                counselors_list = json.load(f)
        except Exception as e:
            print(f"Error loading counselors.json: {e}")

    # Fetch user's scheduled/completed appointments
    user_appointments = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.id.desc()).all()
    
    return render_template('counselors.html', counselors=counselors_list, appointments=user_appointments)


@pages_bp.route('/appointments/create', methods=['POST'])
@login_required
def create_appointment():
    try:
        data = request.get_json(force=True)
        counselor_id = int(data.get('counselor_id'))
        counselor_name = data.get('counselor_name', '').strip()
        appointment_date = data.get('appointment_date', '').strip()
        appointment_time = data.get('appointment_time', '').strip()
        reason = data.get('reason', '').strip()

        if not counselor_id or not counselor_name or not appointment_date or not appointment_time:
            return jsonify({"error": "Counselor, Date, and Time are required"}), 400

        # Save to DB
        appointment = Appointment(
            user_id=current_user.id,
            counselor_id=counselor_id,
            counselor_name=counselor_name,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            reason=reason,
            status="Scheduled"
        )
        db.session.add(appointment)
        db.session.commit()

        return jsonify({
            "message": "Appointment booked successfully!",
            "appointment": appointment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to book appointment: {str(e)}"}), 500

