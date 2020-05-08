import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { PropertyBuilderComponent } from './property-builder.component';
import { MockComponent } from 'ng-mocks';
import { HttpClientModule } from '@angular/common/http';
import { PropertyFormComponent } from './property-form/property-form.component';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick } from 'src/app/shared/models/brick';

describe('PropertyBuilderComponent', () => {

  const MockUploadService = {
    getBrickBuilder: () => new Brick()
  };

  let spectator: Spectator<PropertyBuilderComponent>;
  const createComponent = createComponentFactory({
    component: PropertyBuilderComponent,
    entryComponents: [
      MockComponent(PropertyFormComponent)
    ],
    imports: [
      HttpClientModule
    ],
    providers: [
      mockProvider(UploadService, MockUploadService)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
