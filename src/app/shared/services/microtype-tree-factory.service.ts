import { Injectable } from '@angular/core';
import { MicroTypeTreeNode, MicroTypeTree } from 'src/app/shared/models/microtype-tree';

@Injectable({
  providedIn: 'root'
})
export class MicrotypeTreeFactoryService {

  constructor() { }

  public static createMicrotypeTree(microtypes): MicroTypeTreeNode[] {
    let hashTable = Object.create(null);
    microtypes.results.forEach(microtype => {
        hashTable[microtype.term_id] = {...microtype, children: []}
    });
    let microtypeTree: Array<MicroTypeTreeNode> = [];
    microtypes.results.forEach((microtype: MicroTypeTreeNode) => {
        if(microtype.mt_parent_term_ids.length) {
            microtype.mt_parent_term_ids
              .forEach((id: string) => {
                // there are some items with parents that are not in the results
                if(hashTable[id] !== undefined) {
                    hashTable[id].children.push({...hashTable[microtype.term_id]});
                }
            });
        } else {
            microtypeTree.push(hashTable[microtype.term_id]);
        }
    });
    return microtypeTree;
  }

  filterNonMicrotypes(microtypes: MicroTypeTreeNode[]) {
    // filter out non-microtypes that don't have children

  }
}
