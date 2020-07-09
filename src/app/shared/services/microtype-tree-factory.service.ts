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
      microtype.children = [];
      // filter out ids with parents to roots, results in double values otherwise
      microtype.mt_parent_term_ids = microtype.mt_parent_term_ids
        .filter(id => id !== 'ENIGMA:0000000' && id !== 'ME:0000000');

      microtype.mt_parent_term_ids.forEach(id => {
        // make sure first item in array (ME:0000039) gets added to list
        if ((map[id] || id === 'ME:0000039')) {
          microtypes[map[id]].children.push(microtype);
        } else {
          result.push(microtype);
        }
      });
    });
    return result;
  }
}
