from sqlalchemy.orm import Session

from app.models import Lesson, User

DEMO_LESSONS = [
    Lesson(
        title="小猫 cat",
        text="cat",
        ipa="/kæt/",
        target_phonemes=["æ"],
        level="beginner",
        tip="嘴巴张大一点，发出扁扁的 /æ/。",
    ),
    Lesson(
        title="绵羊 sheep",
        text="sheep",
        ipa="/ʃiːp/",
        target_phonemes=["iː"],
        level="beginner",
        tip="微笑拉长声音，不要发成短短的 ship。",
    ),
    Lesson(
        title="小船 ship",
        text="ship",
        ipa="/ʃɪp/",
        target_phonemes=["ɪ"],
        level="beginner",
        tip="声音短而松，和 sheep 对比着练。",
    ),
    Lesson(
        title="想一想 think",
        text="think",
        ipa="/θɪŋk/",
        target_phonemes=["θ"],
        level="beginner",
        tip="舌尖轻轻伸到牙齿中间吹气。",
    ),
    Lesson(
        title="非常 very",
        text="very",
        ipa="/ˈveri/",
        target_phonemes=["v"],
        level="beginner",
        tip="上牙轻轻咬住下嘴唇，不要发成 we。",
    ),
]


def seed_if_empty(db: Session) -> None:
    if db.query(User).count() == 0:
        db.add(User(nickname="小朋友"))
    if db.query(Lesson).count() == 0:
        db.add_all(DEMO_LESSONS)
    db.commit()
