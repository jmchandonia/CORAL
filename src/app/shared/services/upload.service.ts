import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import {
  Brick,
  BrickDimension,
  TypedProperty,
  Term,
  DimensionVariable
 } from 'src/app/shared/models/brick';
import { environment } from 'src/environments/environment';
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
    return this.http.get(`${environment.baseURL}/data_types`);
  }

  getBrickTypeTemplates() {
    return this.http.get(`${environment.baseURL}/brick_type_templates`);
  }

  getDataModels() {
    return this.http.get(`${environment.baseURL}/data_models`);
  }
}
