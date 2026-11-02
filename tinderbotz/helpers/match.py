from tinderbotz.helpers.geomatch import Geomatch

# A match has the same information as a geomatch, except that you have a chatroom with an id
class Match(Geomatch):

    def __init__(self, name, chatid, age, work, study, home, gender, bio, distance, passions, image_urls):
        self.chatid = chatid

        # invoking the __init__ of the parent class
        super().__init__(
            name=name, age=age, work=work, study=study, home=home,
            gender=gender, bio=bio, lifestyle=None, basics=None, anthem=None,
            distance=distance, passions=passions, image_urls=image_urls,
        )

    def get_chat_id(self):
        return self.chatid

    def get_dictionary(self):
        data = {
            "name": self.get_name(),
            "age": self.get_age(),
            "work": self.get_work(),
            "study": self.get_study(),
            "home": self.get_home(),
            "gender": self.get_gender(),
            "bio": self.get_bio(),
            "distance": self.get_distance(),
            "passions": self.get_passions(),
            "image_urls": self.image_urls,
            "images_by_hashes": self.images_by_hashes,
            "chatid": self.get_chat_id()
        }
        return data
