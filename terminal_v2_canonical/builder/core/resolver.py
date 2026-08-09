from dataclasses import dataclass

@dataclass
class Dependency:

    name:str

    requires:list

class Resolver:

    def __init__(self):

        self.items=[]

    def add(self,name,*requires):

        self.items.append(
            Dependency(
                name,
                list(requires)
            )
        )

    def resolve(self):

        ordered=[]

        seen=set()

        while len(ordered)!=len(self.items):

            progress=False

            for item in self.items:

                if item.name in seen:
                    continue

                if all(x in seen for x in item.requires):

                    ordered.append(item.name)

                    seen.add(item.name)

                    progress=True

            if not progress:

                raise RuntimeError(
                    "Dependency cycle detected."
                )

        return ordered
