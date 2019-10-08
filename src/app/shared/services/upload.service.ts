import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  Brick,
  BrickDimension,
  TypedProperty,
  Term,
  DimensionVariable
 } from 'src/app/shared/models/brick';
@Injectable({
  providedIn: 'root'
})
export class UploadService {

  public brickBuilder: Brick = new Brick();

  getBrickBuilder() {
    return this.brickBuilder;
  }

  testBrickBuilder() {
    console.log('CURRENT BRICK OBJECT', this.brickBuilder);
  }

  constructor(
    private http: HttpClient
  ) { }

  getDataTypes() {
    return this.http.get('https://psnov1.lbl.gov:8082/generix/data_types');
  }

  getDataModels() {
    return this.http.get('https://psnov1.lbl.gov:8082/generix/data_models');
  }
}
