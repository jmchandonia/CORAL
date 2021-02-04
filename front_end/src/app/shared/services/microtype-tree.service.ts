import { Injectable } from '@angular/core';
import { MicrotypeTreeFactoryService as MicrotypeTreeFactory } from './microtype-tree-factory.service';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';
import { MicroTypeTreeNode } from '../models/microtype-tree';

@Injectable({
  providedIn: 'root'
})
export class MicrotypeTreeService {

  microtypes: MicroTypeTreeNode[];

  constructor(private http: HttpClient) {
  }

  getMicrotypes(): Promise<MicroTypeTreeNode[]> {
    return new Promise((resolve, reject) => {
      this.http.get(`${environment.baseURL}/microtypes`).subscribe((data: any) => {
        this.microtypes = MicrotypeTreeFactory.createMicrotypeTree(data.results);
        resolve(this.microtypes);
      })
    });
  }
}
