import { Injectable } from '@angular/core';
import { MicroTypeTreeNode, MicroTypeTree } from 'src/app/shared/models/microtype-tree';

@Injectable({
  providedIn: 'root'
})
export class MicrotypeTreeFactoryService {

  constructor() { }

  public static createMicrotypeTree(microtypes): MicroTypeTreeNode[] {
    const result = [];
    const map = {};

    microtypes.forEach((microtype, idx) => {
      map[microtype.term_id] = idx;
      microtypes[idx].children = [];
      microtype.mt_parent_term_ids.forEach(id => {
        if (map[id]) {
          microtypes[map[id]].children.push(microtype);
        } else {
          result.push(microtype);
        }
      });
    });
    return result;
  }
}
