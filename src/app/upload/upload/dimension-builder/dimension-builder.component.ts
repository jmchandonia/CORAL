import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-dimension-builder',
  templateUrl: './dimension-builder.component.html',
  styleUrls: ['./dimension-builder.component.css']
})
export class DimensionBuilderComponent implements OnInit {

  brick: Brick;

  constructor(
    private uploadService: UploadService
  ) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
  }

  addDimension() {
    this.brick.dimensions.push(new BrickDimension(this.brick, this.brick.dimensions.length));
  }

  removeDimension(dimension) {
    this.brick.dimensions = this.brick.dimensions.filter(dim => dim !== dimension);
    this.brick.resetDimensionIndices();
  }

}
