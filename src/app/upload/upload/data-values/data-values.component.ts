import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, DataValue } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-data-values',
  templateUrl: './data-values.component.html',
  styleUrls: ['./data-values.component.css']
})
export class DataValuesComponent implements OnInit {

  constructor(private uploadService: UploadService) { }

  dataValues: DataValue[];
  brick: Brick;

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.dataValues = this.brick.dataValues;
  }

  addDataValue() {
    this.dataValues.push(new DataValue(this.dataValues.length, false));
  }

  removeDataValue(index) {
    this.brick.dataValues = this.brick.dataValues.splice(index, 1);
    this.brick.resetDataValueIndices();
  }

}
