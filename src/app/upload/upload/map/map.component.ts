import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, BrickDimension, DimensionVariable, TypedProperty } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-map',
  templateUrl: './map.component.html',
  styleUrls: ['./map.component.css']
})
export class MapComponent implements OnInit {

  brick: Brick;
  dimVars: DimensionVariable[] = [];

  constructor(private uploadService: UploadService) { }

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.brick.dimensions.forEach(dim => {
      this.dimVars = [...this.dimVars, ...dim.variables];
    });
    console.log('DIM VARS', this.dimVars);
  }

}
