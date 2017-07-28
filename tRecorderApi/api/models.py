from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.forms.models import model_to_dict
from django.utils.timezone import now
import urllib2
import pickle
import json
import os


class Language(models.Model):
    slug = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=100, blank=True)

    @staticmethod
    def getLanguagesList():
        lst = []
        projects = Project.objects.filter(is_source=False)
        for project in projects:
            if project.version and project.language and project.book:
                lst.append(model_to_dict(project.language))

        # distinct list
        lst = list({v['id']: v for v in lst}.values())
        return lst

    @staticmethod
    def getLanguageByCode(code):
        url = 'http://td.unfoldingword.org/exports/langnames.json'
        languages = []
        try:
            response = urllib2.urlopen(url)
            languages = json.loads(response.read())
            with open('language.json', 'wb') as fp:
                pickle.dump(languages, fp)
        except urllib2.URLError, e:
            with open('language.json', 'rb') as fp:
                languages = pickle.load(fp)

        ln = ""
        for dicti in languages:
            if dicti["lc"] == code:
                ln = dicti["ln"]
                break
        return ln

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return self.name


class Book(models.Model):
    slug = models.CharField(max_length=3, unique=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    booknum = models.IntegerField(default=0)

    @staticmethod
    def getBooksList():
        lst = []
        projects = Project.objects.filter(is_source=False)
        for project in projects:
            if project.version and project.language and project.book:
                lst.append(model_to_dict(project.book))

        # distinct list
        lst = list({v['id']: v for v in lst}.values())
        return lst

    @staticmethod
    def getBookByCode(code):
        with open('books.json') as books_file:
            books = json.load(books_file)

        bn = ""
        for dicti in books:
            if dicti["slug"] == code:
                bn = dicti["name"]
                break
        return bn

    class Meta:
        ordering = ["booknum"]

    def __unicode__(self):
        return self.name


class User(models.Model):
    name = models.CharField(max_length=50)
    agreed = models.BooleanField()
    picture = models.CharField(max_length=250)

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return self.name


class Comment(models.Model):
    location = models.CharField(max_length=250)
    date_modified = models.DateTimeField(default=now)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ["date_modified"]

    def __unicode__(self):
        return self.location


class Project(models.Model):
    version = models.CharField(max_length=3, blank=True)
    mode = models.CharField(max_length=10, blank=True)
    anthology = models.CharField(max_length=2, blank=True)
    is_source = models.BooleanField(default=False)
    is_publish = models.BooleanField(default=False)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, null=True, blank=True)
    source_language = models.ForeignKey(Language, related_name="language_source", null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)

    @staticmethod
    def getProjects(data):
        lst = []
        filter = {}

        if "language" in data:
            filter["language__slug"] = data["language"]
        if "version" in data:
            filter["version"] = data["version"]
        if "book" in data:
            filter["book__slug"] = data["book"]
        if "is_publish" in data:
            filter["is_publish"] = data["is_publish"]

        filter["is_source"] = False
        projects = Project.objects.filter(**filter)

        for project in projects:
            if not project.version or not project.language or not project.book:
                continue

            dic = {}

            dic["id"] = project.id
            dic["version"] = project.version
            dic["is_publish"] = project.is_publish

            latest_take = Take.objects.filter(chunk__chapter__project=project) \
                .latest("date_modified")
            # Get contributors
            dic["contributors"] = []
            dic["date_modified"] = latest_take.date_modified
            availChunks = 0
            checklvl = 10
            chapters = project.chapter_set.all()
            for chapter in chapters:
                availChunks += 1
                if chapter.checked_level < checklvl:
                    checklvl = chapter.checked_level
                chunks = chapter.chunk_set.all()
                for chunk in chunks:
                    availChunks += 1
                    takes = chunk.take_set.all()
                    for take in takes:
                        try:
                            if take.user.name not in dic["contributors"]:
                                dic["contributors"].append(take.user.name)
                        except:
                            pass

            dic["checked_level"] = checklvl
            mode = project.mode
            bkname = project.book.slug
            chunkInfo = []
            for dirpath, dirnames, files in os.walk(os.path.abspath('static/chunks/')):
                if dirpath[-3:] == bkname:
                    for fname in os.listdir(dirpath):
                        f = open(os.path.join(dirpath, fname), "r")
                        sus = json.loads(f.read())
                        chunkInfo = sus
                    break
            totalChunk = float(len(chunkInfo))
            completed = int(round((availChunks / totalChunk) * 100))
            dic["completed"] = completed

            # Get language
            try:
                dic["language"] = model_to_dict(project.language,
                                                fields=["slug", "name"])
            except:
                pass

            # Get book
            try:
                dic["book"] = model_to_dict(project.book,
                                            fields=["booknum", "slug", "name"])
            except:
                pass

            lst.append(dic)

        return lst

    @staticmethod
    def getVersionsByProject():
        lst = []
        projects = Project.objects.filter(is_source=False)
        for project in projects:
            if project.version and project.language and project.book:
                lst.append(project.version)

        # distinct list
        lst = list(set(lst))
        return lst

    class Meta:
        ordering = ["language", "version", "book"]

    def __unicode__(self):
        return '{}-{}-{} ({})'.format(self.language, self.version, self.book, self.id)


class Chapter(models.Model):
    number = models.IntegerField(default=0)
    checked_level = models.IntegerField(default=0)
    is_publish = models.BooleanField(default=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    comments = GenericRelation(Comment)

    @staticmethod
    def getChaptersByProject(data):
        dic = {}
        filter = {}

        filter["language__slug"] = data["language"]
        filter["version"] = data["version"]
        filter["book__slug"] = data["book"]
        filter["is_source"] = False

        projects = Project.objects.filter(**filter)

        for project in projects:
            # Get chapters

            if not project.version or not project.language or not project.book:
                continue

            mode = project.mode
            bkname = project.book.slug

            latest_take = Take.objects.filter(chunk__chapter__project=project) \
                .latest("date_modified")

            chaps = []
            chapters = project.chapter_set.all()
            for chapter in chapters:
                chap_dic = {}
                chap_dic["id"] = chapter.id
                chap_dic["chapter"] = chapter.number
                chap_dic["checked_level"] = chapter.checked_level
                chap_dic["is_publish"] = chapter.is_publish

                # contains information about all chunks in a book
                chunkInfo = []
                for dirpath, dirnames, files in os.walk(os.path.abspath('static/chunks/')):
                    if dirpath[-3:] == bkname:
                        for fname in os.listdir(dirpath):
                            f = open(os.path.join(dirpath, fname), "r")
                            sus = json.loads(f.read())
                            chunkInfo = sus
                        break
                # contains info about relevant chapter
                chunkstuff = []
                chapnum = chapter.number
                for chunk in chunkInfo:
                    if chunk["id"][:2] == str("%02d" % chapnum):
                        chunkstuff.append(chunk)
                chunks = chapter.chunk_set.all()

                percentComplete = 0

                if len(chunks) > 0:
                    numtakes = list(chunks)
                    if mode == "chunk":
                        percentComplete = int(round(len(numtakes)/(len(chunkstuff))* 100))
                    else:
                        versetotal = 0
                        for i in chunkstuff:
                            if int(i["lastvs"]) > versetotal:
                                versetotal = int(i["lastvs"])
                        percentComplete = int(round((len(numtakes)/versetotal) * 100))

                chap_dic["percent_complete"] = percentComplete
                chap_dic["date_modified"] = latest_take.date_modified

                # Get contributors
                chap_dic["contributors"] = []
                chunks = chapter.chunk_set.all()
                for chunk in chunks:
                    takes = chunk.take_set.all()
                    for take in takes:
                        try:
                            if take.user.name not in chap_dic["contributors"]:
                                chap_dic["contributors"].append(take.user.name)
                        except:
                            pass

                # Get comments
                chap_dic["comments"] = []
                for cmt in chapter.comments.all():
                    dic2 = {}
                    dic2["comment"] = model_to_dict(cmt, fields=["location", "date_modified"])
                    # Include author of comment
                    try:
                        dic2["user"] = model_to_dict(cmt.user, fields=["name", "agreed", "picture"])
                    except:
                        pass
                    chap_dic["comments"].append(dic2)

                chaps.append(chap_dic)

            dic["chapters"] = chaps

            # Get language
            try:
                dic["language"] = model_to_dict(project.language,
                                                fields=["slug", "name"])
            except:
                dic["language"] = {}

            # Get book
            try:
                dic["book"] = model_to_dict(project.book,
                                            fields=["booknum", "slug", "name"])
            except:
                dic["language"] = {}
            # Get Project ID
            try:
                dic["project_id"] = project.id
            except:
                dic["project_id"] = {}
            # Get is_publish
            try:
                dic["is_publish"] = project.is_publish
            except:
                dic["is_publish"] = {}
        return dic

    class Meta:
        ordering = ["number"]

    def __unicode__(self):
        return '{}'.format(self.number)


class Chunk(models.Model):
    startv = models.IntegerField(default=0)
    endv = models.IntegerField(default=0)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, null=True, blank=True)
    comments = GenericRelation(Comment)

    @staticmethod
    def getChunksWithTakesByProject(data):
        data_dic = {}
        chunks_list = []
        filter = {}

        if "project" in data:
            filter["chapter__project"] = data["project"]
        if "language" in data:
            filter["chapter__project__language__slug"] = data["language"]
        if "version" in data:
            filter["chapter__project__version"] = data["version"]
        if "book" in data:
            filter["chapter__project__book__slug"] = data["book"]
        if "mode" in data:
            filter["chapter__project__mode"] = data["mode"]
        if "chapter" in data:
            filter["chapter__number"] = data["chapter"]
        if "startv" in data:
            filter["startv"] = data["startv"]
        if "endv" in data:
            filter["endv"] = data["endv"]

        chunks = Chunk.objects.filter(**filter)

        data_dic["chunks"] = []

        for chunk in chunks:
            chunk_dic = {}

            # Include language data
            try:
                if "language" not in data_dic:
                    data_dic["language"] = model_to_dict(chunk.chapter.project.language,
                                                         fields=["slug", "name"])
            except:
                pass
            # Include book data
            try:
                if "book" not in data_dic:
                    data_dic["book"] = model_to_dict(chunk.chapter.project.book,
                                                     fields=["booknum", "slug", "name"])
            except:
                pass

            # Include project data
            try:
                if "project" not in data_dic:
                    data_dic["project"] = model_to_dict(chunk.chapter.project,
                        fields=["id","is_publish", "version",
                            "mode", "anthology"])
            except:
                pass

            # Include chapter data
            try:
                if "chapter" not in data_dic:
                    data_dic["chapter"] = model_to_dict(chunk.chapter,
                                                        fields=["id", "is_publish", "number",
                                                                "checked_level", "comments"])

                    # Include comments for chapter
                    data_dic["chapter"]["comments"] = []
                    for cmt in chunk.chapter.comments.all():
                        comm_dic = {}
                        comm_dic["comment"] = model_to_dict(cmt, fields=["id", "location", "date_modified"])
                        # Include author of comment
                        try:
                            comm_dic["user"] = model_to_dict(cmt.user, fields=["name", "agreed", "picture"])
                        except:
                            pass
                        data_dic["chapter"]["comments"].append(comm_dic)
            except:
                pass

            # Include comments for chunk
            chunk_dic["comments"] = []
            for cmt in chunk.comments.all():
                comm_dic = {}
                comm_dic["comment"] = model_to_dict(cmt, fields=["id", "location", "date_modified"])
                # Include author of comment
                try:
                    comm_dic["user"] = model_to_dict(cmt.user, fields=["name", "agreed", "picture"])
                except:
                    pass
                chunk_dic["comments"].append(comm_dic)

            # Include source file if any / TODO remove source from code and db
            """source_language = chunk.chapter.project.source_language
            if source_language and chunk.chapter.project.book:
                source_dic = {}
                source_dic["language"] = model_to_dict(source_language, fields=["slug","name"])

                source_take = Take.objects \
                    .filter(chunk__chapter__project__language__slug=source_dic["language"]["slug"]) \
                    .filter(chunk__chapter__project__version=data_dic["project"]["version"]) \
                    .filter(chunk__chapter__project__book__slug=data_dic["book"]["slug"]) \
                    .filter(chunk__chapter__project__mode=data_dic["project"]["mode"]) \
                    .filter(chunk__chapter__number=data_dic["chapter"]["number"]) \
                    .filter(chunk__startv=chunk.startv) \
                    .filter(chunk__endv=chunk.endv) \
                    .filter(chunk__chapter__project__is_source=True) \
                    .first()
                if source_take:
                    if source_take.markers:
                        source_take.markers = json.loads(source_take.markers)
                    else:
                        source_take.markers = {}

                    source_dic["take"] = model_to_dict(source_take, fields=[
                        "markers","location","id"
                    ])
                    source_dic["take"]["version"] = source_take.chunk.chapter.project.version
                    chunk_dic["source"] = source_dic"""

            # Include takes
            takes_list = []
            for take in chunk.take_set.all():
                if "is_publish" in data:
                    if take.is_publish != data["is_publish"]:
                        continue

                take_dic = {}

                # Include author of file
                try:
                    take_dic["user"] = model_to_dict(take.user, fields=["name", "agreed", "picture"])
                except:
                    pass

                # Include comments for chunks
                take_dic["comments"] = []
                # for cmt in Comment.objects.filter(content_type=take.id).values():
                for cmt in take.comments.all():
                    comm_dic = {}
                    comm_dic["comment"] = model_to_dict(cmt, fields=["id", "location", "date_modified"])
                    # Include author of comment
                    try:
                        comm_dic["user"] = model_to_dict(cmt.user, fields=["name", "agreed", "picture"])
                    except:
                        pass
                    take_dic["comments"].append(comm_dic)

                # Parse markers
                if take.markers:
                    take.markers = json.loads(take.markers)
                else:
                    take.markers = {}

                take_dic["take"] = model_to_dict(take, fields=[
                    "location", "duration", "rating",
                    "date_modified", "markers", "id",
                    "is_publish"
                ])

                takes_list.append(take_dic)

            chunk_dic["takes"] = takes_list

            chunk_dic2 = model_to_dict(chunk, fields=[
                "startv", "endv", "id"
            ])

            chunk_dic = dict(chunk_dic.items() + chunk_dic2.items())

            data_dic["chunks"].append(chunk_dic)
        return data_dic

    class Meta:
        ordering = ["startv"]

    def __unicode__(self):
        return '{}:{}-{}'.format(
            self.chapter.number,
            self.startv,
            self.endv)


class Take(models.Model):
    location = models.CharField(max_length=250)
    duration = models.IntegerField(default=0)
    rating = models.IntegerField(default=0)
    is_publish = models.BooleanField(default=False)
    markers = models.TextField(null=True, blank=True)
    date_modified = models.DateTimeField(default=now)

    chunk = models.ForeignKey(Chunk, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    comments = GenericRelation(Comment)

    @staticmethod
    def stitchSource(data):
        list = []
        filter = {}
        filter["chapter__project__language__slug"] = data["language"]
        filter["chapter__project__version"] = data["version"]
        filter["chapter__project__book__slug"] = data["book"]
        filter["chapter__number"] = data["chapter"]

        res = Chunk.objects.filter(**filter)
        return res

    @staticmethod
    def updateTakesByProject(data):
        lst = []
        filter = {}
        fields = data["fields"]

        if "project" in data["filter"]:
            filter["chunk__chapter__project"] = data["filter"]["project"]
        if "language" in data["filter"]:
            filter["chunk__chapter__project__language__slug"] = data["filter"]["language"]
        if "version" in data["filter"]:
            filter["chunk__chapter__project__version"] = data["filter"]["version"]
        if "book" in data["filter"]:
            filter["chunk__chapter__project__book__slug"] = data["filter"]["book"]
        if "chapter" in data["filter"]:
            filter["chunk__chapter__number"] = data["filter"]["chapter"]
        if "startv" in data["filter"]:
            filter["chunk__startv"] = data["filter"]["startv"]
        if "is_publish" in data["filter"]:
            filter["chunk__chapter__is_publish"] = data["filter"]["is_publish"]

        return Take.objects.filter(**filter).update(**fields)

    @staticmethod
    def prepareDataToSave(meta, relpath, data, is_source=False):
        dic = {}

        # Create Language in database if it's not there
        language, l_created = Language.objects.get_or_create(
            slug=meta["language"],
            defaults={
                'slug': meta['language'],
                'name': data['langname']},
        )
        dic["language"] = model_to_dict(language)

        # Create Book in database if it's not there
        book, b_created = Book.objects.get_or_create(
            slug=meta["slug"],
            defaults={
                'slug': meta['slug'],
                'booknum': meta['book_number'],
                'name': data['bookname']},
        )
        dic["book"] = model_to_dict(book)

        # Create Project in database if it's not there
        project, p_created = Project.objects.get_or_create(
            version=meta["version"],
            mode=meta["mode"],
            anthology=meta["anthology"],
            language=language,
            book=book,
            is_source=is_source,
            defaults={
                'version': meta['version'],
                'mode': meta['mode'],
                'anthology': meta['anthology'],
                'language': language,
                'book': book,
                'is_source': is_source},
        )
        dic["project"] = model_to_dict(project)

        # Create Chapter in database if it's not there
        chapter, cr_created = Chapter.objects.get_or_create(
            project=project,
            number=meta['chapter'],
            defaults={
                'number': meta['chapter'],
                'checked_level': 0,  # TODO get checked_level from tR
                'project': project},
        )
        dic["chapter"] = model_to_dict(chapter)

        # Create Chunk in database if it's not there
        chunk, ck_created = Chunk.objects.get_or_create(
            chapter=chapter,
            startv=meta['startv'],
            endv=meta['endv'],
            defaults={
                'startv': meta['startv'],
                'endv': meta['endv'],
                'chapter': chapter},
        )
        dic["chunk"] = model_to_dict(chunk)

        markers = json.dumps(meta['markers'])

        # If the take came from .tr file (Source audio)
        # then check if it exists in database
        # if it exists then update it's data
        # otherwise create new record
        # TODO remove source files functionality
        if (is_source):
            defaults = {
                'location': relpath,
                'duration': data['duration'],
                'rating': 0,  # TODO get rating from tR
                'markers': markers,
            }
            try:
                obj = Take.objects.get(
                    chunk=chunk,
                )
                if os.path.exists(obj.location):
                    os.remove(obj.location)
                for key, value in defaults.items():
                    setattr(obj, key, value)
                obj.save()
            except Take.DoesNotExist:
                new_values = {
                    'chunk': chunk,
                }
                new_values.update(defaults)
                obj = Take(**new_values)
                obj.save()
        else:
            take = Take(location=relpath,
                        duration=data['duration'],
                        rating=0,  # TODO get rating from tR
                        markers=markers,
                        user_id=1,
                        chunk=chunk)  # TODO get author of file and save it to Take model
            take.save()
        return dic

    class Meta:
        ordering = ["chunk"]

    def __unicode__(self):
        return '{} ({})'.format(self.chunk, self.id)
