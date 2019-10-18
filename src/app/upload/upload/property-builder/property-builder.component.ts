import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, TypedProperty } from 'src/app/shared/models/brick';

@Component({
  selector: 'app-property-builder',
  templateUrl: './property-builder.component.html',
  styleUrls: ['./property-builder.component.css']
})
export class PropertyBuilderComponent implements OnInit {

  public properties: TypedProperty[];
  brick: Brick;
  propertyList: any[];

  constructor(
    private uploadService: UploadService
  ) {
    this.brick = uploadService.getBrickBuilder();
    this.properties = this.brick.properties;
   }

  ngOnInit() {
    this.uploadService.getDataModels()
      .subscribe((data: any) => {
        // starting out upload wizard with just brick types
        this.propertyList = data.results.Brick.properties;
      });
  }

  addProperty() {
    this.properties.push(new TypedProperty(this.properties.length, true));
    this.uploadService.testBrickBuilder();
  }

  deleteProperty(property) {
    this.brick.properties = this.brick.properties.filter(item => item !== property);
    this.properties = this.brick.properties;
  }

}
