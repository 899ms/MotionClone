from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


MAX_DURATION = 120


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Keyframe(Strict):
    t: float = Field(ge=0, le=MAX_DURATION)
    x: float = Field(default=.1, ge=-2, le=2)
    y: float = Field(default=.4, ge=-2, le=2)
    w: float = Field(default=.8, gt=0, le=3)
    h: float = Field(default=.15, gt=0, le=3)
    opacity: float = Field(default=1, ge=0, le=1)
    rotation: float = Field(default=0, ge=-360, le=360)
    blur: float = Field(default=0, ge=0, le=30)
    reveal: float = Field(default=1, ge=0, le=1)


class Track(Strict):
    id: str = Field(max_length=80)
    kind: Literal['text','rect','ellipse','line','image','gradient']
    start: float = Field(default=0, ge=0, le=MAX_DURATION)
    end: float = Field(default=5, gt=0, le=MAX_DURATION)
    text: str = Field(default='', max_length=500)
    color: str = Field(default='#ffffff', pattern=r'^#[0-9a-fA-F]{6}$')
    color2: str = Field(default='#000000', pattern=r'^#[0-9a-fA-F]{6}$')
    font: Literal['sans','serif','mono'] = 'sans'
    weight: Literal['regular','bold'] = 'bold'
    align: Literal['left','center','right'] = 'center'
    size: float = Field(default=.08, gt=0, le=1)
    radius: float = Field(default=.02, ge=0, le=1)
    stroke: float = Field(default=0, ge=0, le=.1)
    asset: Literal['logo','none'] = 'none'
    easing: Literal['linear','smooth','out','step'] = 'linear'
    keyframes: list[Keyframe] = Field(default_factory=lambda:[Keyframe(t=0)], min_length=1, max_length=160)

    @model_validator(mode='after')
    def timing(self):
        if self.end <= self.start: raise ValueError('Layer end must be after start.')
        self.keyframes.sort(key=lambda k:k.t)
        return self


class Mask(Strict):
    id: str = Field(max_length=80)
    start: float = Field(ge=0, le=MAX_DURATION)
    end: float = Field(gt=0, le=MAX_DURATION)
    method: Literal['gradient','solid','inpaint'] = 'gradient'
    color: str = Field(default='#ffffff', pattern=r'^#[0-9a-fA-F]{6}$')
    keyframes: list[Keyframe] = Field(min_length=1, max_length=160)

    @model_validator(mode='after')
    def timing(self):
        if self.end <= self.start: raise ValueError('Mask end must be after start.')
        self.keyframes.sort(key=lambda k:k.t)
        return self


class Plan(Strict):
    title: str = Field(default='Untitled film', max_length=160)
    summary: str = Field(default='', max_length=3000)
    observations: list[str] = Field(default_factory=list, max_length=30)
    background: str = Field(default='#101112', pattern=r'^#[0-9a-fA-F]{6}$')
    masks: list[Mask] = Field(default_factory=list, max_length=120)
    tracks: list[Track] = Field(default_factory=list, min_length=1, max_length=160)


class Brief(Strict):
    brand: str = Field(default='', max_length=120)
    instructions: str = Field(default='', max_length=6000)
    mode: Literal['hyperframes','faithful','adapt','rebuild'] = 'hyperframes'
    accent: str = Field(default='#bcf76a', pattern=r'^#[0-9a-fA-F]{6}$')
    keep_audio: bool = True
    auto_review: bool = True
    sampling: Literal['standard','detailed'] = 'standard'


class LibraryUpdate(Strict):
    name: str = Field(default='', min_length=1, max_length=160)
    favorite: bool = False
    archived: bool = False
    collection: str = Field(default='', max_length=80)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode='after')
    def clean(self):
        if 'name' in self.model_fields_set:
            self.name=self.name.strip()
            if not self.name:raise ValueError('Name is required.')
        object.__setattr__(self,'tags',list(dict.fromkeys(t.strip() for t in self.tags if t.strip())))
        if any(len(t)>40 for t in self.tags):raise ValueError('Tags must be 40 characters or fewer.')
        object.__setattr__(self,'collection',self.collection.strip())
        return self


class Review(Strict):
    summary: str = Field(max_length=3000)
    observations: list[str] = Field(max_length=30)
    replace_tracks: list[Track] = Field(max_length=160)
    replace_masks: list[Mask] = Field(max_length=120)
    remove_tracks: list[str] = Field(max_length=160)
    remove_masks: list[str] = Field(max_length=120)


def apply_review(plan: Plan, review: Review):
    data=plan.model_dump()
    for key in ['tracks','masks']:
        replacements={x.id:x.model_dump() for x in getattr(review,'replace_'+key)}
        removed=set(getattr(review,'remove_'+key))
        items=[]
        for old in data[key]:
            if old['id'] not in removed:items.append(replacements.pop(old['id'],old))
        items.extend(x for id,x in replacements.items() if id not in removed)
        data[key]=items
    data['summary']=review.summary;data['observations']=review.observations
    return Plan.model_validate(data)


def output_schema(model=Plan):
    schema = model.model_json_schema()
    def strict(node):
        if isinstance(node, dict):
            node.pop('default', None)
            if node.get('type') == 'object':
                node['additionalProperties'] = False
                node['required'] = list(node.get('properties', {}))
            for v in node.values(): strict(v)
        elif isinstance(node, list):
            for v in node: strict(v)
    strict(schema)
    return schema
