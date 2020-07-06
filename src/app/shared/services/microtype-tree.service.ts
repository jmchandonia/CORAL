import { Injectable } from '@angular/core';
import { MicrotypeTreeFactoryService as MicrotypeTreeFactory } from './microtype-tree-factory.service';
import { HttpClient } from '@angular/common/http';
import { MicroTypeTreeNode } from '../models/microtype-tree';
const mockMicrotypes = require('src/app/shared/test/mock_microtypes.json');

@Injectable({
  providedIn: 'root'
})
export class MicrotypeTreeService {

  microtypes: MicroTypeTreeNode[];

  constructor(private http: HttpClient) {
    // this.getMicrotypes();
  }

  getMicrotypes(): Promise<MicroTypeTreeNode[]> {
    return new Promise((resolve, reject) => {
      this.microtypes = mockMicrotypes;
      resolve(this.microtypes);
    });
  }
}
